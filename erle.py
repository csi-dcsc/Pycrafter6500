'''
copied from this repository
https://github.com/e841018/ERLE

@author Ashu
'''

# encode image of shape (n<=24, 1080, 1920) with Enhanced Run-Length Encoding (ERLE) described in http://www.ti.com/lit/pdf/dlpu018

import numpy as np
import struct
pack32be = struct.Struct('>I').pack  # uint32 big endian


def get_header():
    '''
    generate header defined in section 2.4.2
    '''
    header = bytearray(0)
    # signature
    header += bytearray([0x53, 0x70, 0x6c, 0x64])
    # width
    header += bytearray([1920 % 256, 1920//256])
    # height
    header += bytearray([1080 % 256, 1080//256])
    # number of bytes, will be overwritten later
    header += bytearray(4)
    # reserved
    header += bytearray([0xff]*8)
    # background color (BB GG RR 00)
    header += bytearray(4)
    # reserved
    header.append(0)
    # compression, 0=Uncompressed, 1=RLE, 2=Enhanced RLE
    header.append(2)
    # reserved
    header.append(1)
    header += bytearray(21)
    return header

header_template = get_header()


def merge(images):
    '''
    merge up to 24 binary images into a single 24-bit image, each pixel is an uint32 of format 0x00BBGGRR
    '''
    image32 = np.zeros((1080, 1920), dtype=np.uint32)
    n_img = len(images)
    batches = [8]*(n_img//8)
    if n_img % 8:
        batches.append(n_img % 8)
    for i, batch_size in enumerate(batches):
        image8 = np.zeros((1080, 1920), dtype=np.uint8)
        for j in range(batch_size):
            image8 += images[i*8+j]*(1 << j)
        image32 += image8*(1 << (i*8))
    return image32


def bgr(pixel):
    '''
    convert an uint32 pixel into [B, G, R] bytes
    '''
    return pack32be(pixel)[1:4]


def enc128(num):
    '''
    encode num (up to 32767) into 1 or 2 bytes
    '''
    return bytearray([(num & 0x7f) | 0x80, num >> 7]) if num >= 128 else bytearray([num])


def run_len(row, idx):
    '''
    find the length of the longest run starting from idx in row
    '''
    stride = 128
    length = len(row)
    j = idx
    while j < length and row[j]:
        if j % stride == 0 and np.all(row[j:j+stride]):
            j += min(stride, length-j)
        else:
            j += 1
    return j-idx


def encode_row(row, same_prev):
    '''
    encode a row of length 1920 with the format described in section 2.4.3.2
    '''
    # bool array indicating if same as previous row, shape = (1920, )
#     same_prev = np.zeros(1920, dtype=bool) if i==0 else image[i]==image[i-1]
    # bool array indicating if same as next element, shape = (1919, )
    same = np.logical_not(np.diff(row))
    # same as previous row or same as next element, shape = (1919, )
    same_either = np.logical_or(same_prev[:1919], same)

    j = 0
    compressed = bytearray(0)
    while j < 1920:

        # copy n pixels from previous line
        if same_prev[j]:
            r = run_len(same_prev, j+1) + 1
            j += r
            compressed += b'\x00\x01' + enc128(r)

        # repeat single pixel n times
        elif j < 1919 and same[j]:
            r = run_len(same, j+1) + 2
            j += r
            compressed += enc128(r) + bgr(row[j-1])

        # single uncompressed pixel
        elif j > 1917 or same_either[j+1]:
            compressed += b'\x01' + bgr(row[j])
            j += 1

        # multiple uncompressed pixels
        else:
            j_start = j
            pixels = bgr(row[j]) + bgr(row[j+1])
            j += 2
            while j == 1919 or not same_either[j]:
                pixels += bgr(row[j])
                j += 1
            compressed += b'\x00' + enc128(j-j_start) + pixels

    return compressed + b'\x00\x00'


def encode(images):
    '''
    encode image with the format described in section 2.4.3.2.1
    '''
    # header
    encoded = bytearray(header_template)

    # uint32 array, shape = (1080, 1920)
    image = merge(images)

    # image content
    for i in range(1080):
        # bool array indicating if same as previous row, shape = (1920, )
        same_prev = np.zeros(1920, dtype=bool) if i == 0 else image[i] == image[i-1]
        encoded += encode_row(image[i], same_prev)

    # end of image
    encoded += b'\x00\x01\x00'

    # pad to 4-byte boundary
    encoded += bytearray((-len(encoded)) % 4)

    # overwrite number of bytes in header
    # uint32 little endian, offset=8
    struct.pack_into('<I', encoded, 8, len(encoded))

    return encoded, len(encoded)
