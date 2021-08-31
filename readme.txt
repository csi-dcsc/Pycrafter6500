Pycrafter 6500 is a native Python controller for Texas Instruments' dlplcr6500evm evaluation module for DLP displays.
The script is compatible with Python 2.x, and should work up to version 3.8 thanks to the kind controbution of Guangyuan Zhao (https://github.com/zhaoguangyuan123). 
The script requires Pyusb and Numpy to be present in your Python environment. The test script included requires the Python Image Library (PIL or pillow) for opening a test image. The device must have libusb drivers installed, for Windows users we suggest to install them= through Zadig (http://zadig.akeo.ie/), and selecting the libusb_win32 driver.

If you use this library for scientific publications, please consider mentioning the library and citing our work (https://doi.org/10.1364/OE.25.000949).

Special thanks to Ashu (@e841018) for contributing a fast encoder to the library, providing a great speedup to the process of loading images to the device.

Features list:

- basic control of the evaluation module (modes selection, idle toggle, start/pause/stop sequences)
- upload of a sequence of EXCLUSIVELY BINARY images for "patterns on the fly" mode, with independent control of exposure times, dark times, triggers and repetitions number.

Quick commands list:

to open a connection with the DMD:

import pycrafter6500
controller=pycrafter6500.dmd()

available functions:

controller.idle_on()
#sets the DMD to idle mode


controller.idle_off()
#wakes the DMD from idle mode


controller.standby()
#sets the DMD to standby


controller.wakeup()
#wakes the DMD from standby


controller.reset()
#resets the DMD


controller.changemode(mode)
#changes the dmd operating mode:
#mode=0 for normal video mode
#mode=1 for pre stored pattern mode
#mode=2 for video pattern mode
#mode=3 for pattern on the fly mode


controller.startsequence()
controller.pausesequence()
controller.stopsequence()


controller.defsequence(images,exposures,trigger in,dark time,trigger out, repetitions)

defines a sequence for pattern on the fly mode. Inputs are:

images: python list of numpy arrays, with size (1080,1920), dtype uint8, and filled with binary values (1 and 0 only)
exposures: python list or numpy array with the exposure times in microseconds of each image. Length must be equal to the images list.
trigger in: python list or numpy array of boolean values determing wheter to wait for an external trigger before exposure. Length must be equal to the images list.
dark time: python list or numpy array with the dark times in microseconds after each image. Length must be equal to the images list.
trigger out: python list or numpy array of boolean values determing wheter to emit an external trigger after exposure. Length must be equal to the images list.
repetitions: number of repetitions of the sequence. set to 0 for infinite loop.
