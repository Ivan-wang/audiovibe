import multiprocessing
from typing import Optional
from queue import Empty

from .streamhandler import AudioStreamEventType, StreamEndException, StreamHandler, StreamState
from .core import StreamEventType, StreamEvent
from .core import StreamError

class StreamProcess(multiprocessing.Process):
    def __init__(self, stream_handler:StreamHandler) -> None:
        super(StreamProcess, self).__init__()

        self.stream_handler = stream_handler
        self.result_queue:Optional[multiprocessing.Queue] = None
        self.task_queue:Optional[multiprocessing.Queue] = None

    def set_event_queues(self, task:multiprocessing.Queue, result:multiprocessing.Queue) -> None:
        self.task_queue = task
        self.result_queue = result

        self.stream_handler.on_seek({'pos': 0})
    
    def unset_event_queues(self) -> None:
        self.task_queue = None
        self.result_queue = None
    
class VibrationProcess(StreamProcess):
    def __init__(self, stream_hander:StreamHandler) -> None:
        super(VibrationProcess, self).__init__(stream_hander)

    def run(self) -> None:
        is_orphan = False # NOTE: vibration without music is an orphan
        if self.task_queue is None or self.result_queue is None:
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
                task = self.task_queue.get(block=True)
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
                        self.result_queue.put(result) 
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
    def __init__(self, stream_handler:StreamHandler) -> None:
        super(AudioProcess, self).__init__(stream_handler)

        # audio process initialize task and result queues for all vibration process
        self.vibration_task_queue = multiprocessing.Queue()
        self.vibration_result_queue = multiprocessing.Queue()

        self.num_vibration_stream = 0
    
    def detach_vibration_proc(self, proc:VibrationProcess) -> None:
        proc.unset_event_queues()
        self.num_vibration_stream -= 1
        self.num_vibration_stream = max(self.num_vibration_stream, 0)

    def attach_vibration_proc(self, proc:VibrationProcess) -> None:
        proc.set_event_queues(self.task_queue, self.result_queue)
        self.num_vibration_stream += 1
    
    def attach_task_queue(self, queue:multiprocessing.Queue) -> None:
        self.task_queue = queue
    
    def attach_result_queue(self, queue:multiprocessing.Queue) -> None:
        self.result_queue = queue
    
    def broadcast_event(self, event:StreamEvent) -> None:
        if event.head == AudioStreamEventType.AUDIO_RESUME:
            # TODO: force all stream aligned
            event.what.setdefault('pos', self.stream_handler.tell())
        for _ in range(self.num_vibration_stream):
            self.vibration_task_queue.put(event) # tasks
    
    def run(self):
        # IMPORTANT: initialize the audio within one process
        # Don't share it across different processes
        while True:
            # IDEA: STEP 1, acquire control messages
            try:
                task = self.task_queue.get(
                    block=not self.stream_handler.is_activate()
                ) # when stream is inactive, wait for next control signal
            except Empty:
                task = None
                pass # no task from main process
            else:
                self.broadcast_event(task)
                self.stream_handler.handle(task)
                # NOTE: break 1, music stream close command
                if task.head == StreamEventType.STREAM_CLOSE:
                    break
            
            # IDEA: STEP 2, handle ack messages
            if task is not None and task.head == StreamEventType.STREAM_STATUS_ACQ:
                # TODO: collect stream response
                pass
            
            # IDEA: STEP 3, always procceed with next frame when activate
            if self.stream_handler.is_activate():
                self.broadcast_event(StreamEvent(head=StreamEventType.STREAM_NEXT_FRAME, what={}))

                try:
                    self.stream_handler.on_next_frame()
                except StreamEndException:
                    # NOTE: break 2, music stream ends
                    self.broadcast_event(StreamEvent(head=StreamEventType.STREAM_CLOSE, what={}))
                    self.stream_handler.on_close()
                    break
                except Exception as e:
                    # NOTE: break 3, music playing errors
                    print(f'playing error {e}')
                    break
        
        # IDEA: STEP 4, before exit, check and try to close handler, no exception raised
        if self.stream_handler.is_activate():
            try:
                self.stream_handler.on_close()
            except:
                pass
