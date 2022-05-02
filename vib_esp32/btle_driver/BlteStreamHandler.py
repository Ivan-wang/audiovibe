import sys
from typing import Optional, Dict

sys.path.append('..')

from vib_music import StreamHandler
from vib_music import StreamDataBase, StreamDriverBase
from vib_music import AudioStreamEventType
from vib_music import StreamState
from vib_music.streamhandler import StreamEndException

class BlteStreamHandler(StreamHandler):
    def __init__(self, stream_data: StreamDataBase, stream_driver: StreamDriverBase, block_size:int=256) -> None:
        super().__init__(stream_data, stream_driver)
        self.block_size = block_size # block_len = block_size * frame_len

        self.loaded_frames = 0
        self.control_handle_funcs.update({
            AudioStreamEventType.AUDIO_PULSE: self.on_pulse
        })
    
    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        if not self.is_activate():
            return
        
        if what is not None and 'frame' in what:
            frame = what.get('frame', None)
            if frame is None:
                raise StreamEndException('received empty frame')
        else:
            if self.tell() == self.num_frame():
                raise StreamEndException('no more frames')
            
            if self.loaded_frames == self.tell():
                # read whole block, and reset the stream data pointer
                block = self.stream_data.readframe(self.block_size)
                self.stream_data.setpos(self.loaded_frames)
                self.loaded_frames += self.block_size
                if len(block) != 0:
                    self.stream_driver.on_next_frame({'frame': block})
            elif self.loaded_frames == self.tell() + self.block_size // 2:
                # read half block, and reset the stream data pointer
                block = self.stream_data.readframe(self.block_size // 2)
                self.stream_data.setpos(self.loaded_frames)
                self.loaded_frames += self.block_size // 2
                if len(block) != 0:
                    self.stream_driver.on_next_frame({'frame': block})
            else:
                # read then discard, HACK: improve efficiency
                _ = self.stream_data.readframe()

        
    def on_pulse(self, what:Optional[Dict]=None) -> None:
        self.stream_state = StreamState.STREAM_INACTIVE
        self.loaded_frames = self.tell()
        # notify BT device to stop
        self.stream_driver.on_pulse()

    def on_seek(self, what: Optional[Dict] = None) -> None:
        self.loaded_frames = what['pos']
        return super().on_seek(what)
        