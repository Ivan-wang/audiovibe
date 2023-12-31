from copy import deepcopy
from multiprocessing import Process, Queue
from typing import Dict, List, Optional, Tuple
from queue import Empty

from .streamhandler import AudioStreamEvent, AudioStreamEventType, AudioStreamHandler, StreamEndException, StreamHandler, StreamState
from .core import StreamEventType, StreamEvent
from .core import StreamError

class StreamProcess(Process):
    def __init__(self, stream_handler:StreamHandler) -> None:
        super(StreamProcess, self).__init__()

        self.stream_handler = stream_handler
        self.send_conn:Optional[Queue] = None
        self.recv_conn:Optional[Queue] = None

        self.frame_ack = False

    def set_event_queues(self, recv:Queue, send:Queue) -> None:
        self.recv_conn = recv
        self.send_conn = send

        # self.stream_handler.on_seek({'pos': 0})
    
    def unset_event_queues(self) -> None:
        self.recv_conn = None
        self.send_conn = None
    
    def event_queues(self) -> Tuple[Queue, Queue]:
        return self.recv_conn, self.send_conn
    
    def get_handler(self) -> StreamHandler:
        return self.stream_handler
    
    def enable_frame_ack(self) -> None:
        self.frame_ack = True
    
class VibrationProcess(StreamProcess):
    def __init__(self, stream_hander:StreamHandler) -> None:
        super(VibrationProcess, self).__init__(stream_hander)

    def run(self) -> None:
        is_orphan = False # NOTE: vibration without music is an orphan
        if self.recv_conn is None or self.send_conn is None:
            is_orphan = True
        
        if is_orphan:
            self.stream_handler.on_init()
            while True:
                try:
                    self.stream_handler.on_next_frame()
                except StreamEndException:
                    print('Stream Exausted.')
                    break
                except Exception as e:
                    print(f'Stream Error {e}')
                    break
        else:
            while True:
                task = self.recv_conn.get(block=True)
                try:
                    result = self.stream_handler.handle(task)
                except StreamEndException:
                    break # DEBUG: should not happen, music and vib should be aligned
                except Exception as e:
                    # NOTE: break 1, cannot hand task
                    print(f'for task {task}, vibration stream handler exception {e}')
                    break
                else:
                    if result is not None:
                        self.send_conn.put(result) 
                finally:
                    # NOTE: break 2, music process closed
                    if task.head == StreamEventType.STREAM_CLOSE:
                        break
        
        # before exit, check and try to close handler, no exception raised
        if self.stream_handler.is_activate():
            try:
                self.stream_handler.on_close()
            except:
                pass

class AudioProcess(StreamProcess):
    def __init__(self, stream_handler:AudioStreamHandler) -> None:
        super(AudioProcess, self).__init__(stream_handler)

        # audio process initialize task and result queues for all vibration process
        self.attached_proc_send_conns = []
        self.attached_proc_recv_conns = []

        self.num_vibration_stream = 0
        # to collect from each stream
        self.received_msgs = []
        #
        self.auto_init = False
        self.auto_exit = True
    
    def enable_GUI_mode(self) -> None:
        # self.stream_handler.disable_bar()
        self.enable_auto_init()
        self.enable_manual_exit()
        self.enable_frame_ack()
    
    def enable_auto_init(self) -> None:
        self.auto_init = True

    def enable_manual_exit(self) -> None:
        self.auto_exit = False
    
    def detach_vibration_proc(self, proc:VibrationProcess) -> None:
        recv, send = proc.event_queues()
        self.attached_proc_send_conns.remove(recv)
        self.attached_proc_recv_conns.remove(send)
        self.num_vibration_stream -= 1
        self.num_vibration_stream = max(self.num_vibration_stream, 0)
        proc.unset_event_queues()

    def attach_vibration_proc(self, proc:VibrationProcess) -> None:
        # IDEA: use P2P queues, no. attached procs -> 1 to 2
        recv, send = Queue(), Queue()
        proc.set_event_queues(recv, send)
        self.attached_proc_recv_conns.append(send)
        self.attached_proc_send_conns.append(recv)

        self.num_vibration_stream += 1

    def broadcast_event(self, event:StreamEvent) -> None:
        # NOTE: do not boardcast AUDIO_START and AUDIO_PULSE
        if event.head == AudioStreamEventType.AUDIO_START:
            return
        elif event.head == AudioStreamEventType.AUDIO_PULSE:
            return
        elif event.head == AudioStreamEventType.AUDIO_RESUME:
            # NOTE: resume event aligns all vibration stream
            pos = self.stream_handler.tell()
            sevent = StreamEvent(StreamEventType.STREAM_SEEK, {'pos': pos})
            for send in self.attached_proc_send_conns:
                send.put(sevent)
        else:
            # NOTE: board other events
            for send in self.attached_proc_send_conns:
                send.put(event)
        
    def collect_recvs(self, timeout:float=0.01) -> None:
        if self.num_vibration_stream == 0:
            return

        timeout /= self.num_vibration_stream
        for i in range(len(self.received_msgs)):
            try:
                recv = self.attached_proc_recv_conns[i].get(block=True, timeout=timeout)
            except Empty:
                break
            else:
                self.received_msgs.append(recv)

        if len(self.received_msgs) == self.num_vibration_stream:
            self.send_conn.put(deepcopy(self.received_msgs))
            self.received_msgs = []
    
    def run(self):
        if self.auto_init:
            self.broadcast_event(StreamEvent(head=StreamEventType.STREAM_INIT))
            msg = self.stream_handler.on_init()
            self.send_conn.put(msg)

        while True:
            # IDEA: STEP 1, acquire control messages
            try:
                task = self.recv_conn.get(
                    block=not self.stream_handler.is_activate()
                ) # when stream is inactive, wait for next control signal
            except Empty:
                task = None # no task from main process
            else:
                self.broadcast_event(task)
                self.stream_handler.handle(task)
                # NOTE: break 1, music stream close command
                if task.head == StreamEventType.STREAM_CLOSE:
                    break
            
            # IDEA: STEP 2, handle ack messages
            if task is not None and task.head == StreamEventType.STREAM_STATUS_ACQ:
                # TODO: collect stream response
                self.collect_recvs()
            
            # IDEA: STEP 3, always procceed with next frame when activate
            if self.stream_handler.is_activate():
                self.broadcast_event(StreamEvent(head=StreamEventType.STREAM_NEXT_FRAME))

                try:
                    self.stream_handler.on_next_frame()
                except StreamEndException:
                    # NOTE: break 2, music stream ends
                    if self.auto_exit:
                        self.broadcast_event(StreamEvent(head=StreamEventType.STREAM_CLOSE))
                        self.stream_handler.on_close()
                        break
                    else:
                        self.stream_handler.on_pulse()
                except Exception as e:
                    # NOTE: break 3, music playing errors
                    print(f'playing error {e}')
                    break

                if self.frame_ack:
                    try:
                        self.send_conn.put(AudioStreamEvent(
                            head=AudioStreamEventType.STREAM_STATUS_ACK, what={'pos': self.stream_handler.tell()}))
                    except:
                        pass
        
        # IDEA: STEP 4, before exit, check and try to close handler, no exception raised
        if self.stream_handler.is_activate():
            try:
                self.stream_handler.on_close()
            except:
                pass
