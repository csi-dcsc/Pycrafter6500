import usb.core
import usb.util
import time
import numpy
import sys


##function that converts a number into a bit string of given length

def convlen(a,l):
    b=bin(a)[2:]
    padding=l-len(b)
    b='0'*padding+b

    return b

##function that converts a bit string into a given number of bytes

def bitstobytes(a):
    bytelist=[]
    if len(a)%8!=0:
        padding=8-len(a)%8
        a='0'*padding+a
    for i in range(len(a)//8):
        bytelist.append(int(a[8*i:8*(i+1)],2))

    bytelist.reverse()

    return bytelist

##function that encodes a 8 bit numpy array matrix as a enhanced run lenght encoded string of bits

def mergeimages(images):
    mergedimage=numpy.zeros((1080,1920,3),dtype='uint8')

    for i in range(len(images)):
        if i<8:
            mergedimage[:,:,2]=mergedimage[:,:,2]+images[i]*(2**i)
        if i>7 and i<16:
            mergedimage[:,:,1]=mergedimage[:,:,1]+images[i]*(2**(i-8))
        if i>15 and i<24:
            mergedimage[:,:,0]=mergedimage[:,:,0]+images[i]*(2**(i-16))

    return mergedimage

def encode(image): 


## header creation
    bytecount=48    
    bitstring=[]

    bitstring.append(0x53)
    bitstring.append(0x70)
    bitstring.append(0x6c)
    bitstring.append(0x64)
    
    width=convlen(1920,16)
    width=bitstobytes(width)
    for i in range(len(width)):
        bitstring.append(width[i])

    height=convlen(1080,16)
    height=bitstobytes(height)
    for i in range(len(height)):
        bitstring.append(height[i])


    total=convlen(0,32)
    total=bitstobytes(total)
    for i in range(len(total)):
        bitstring.append(total[i])        

    for i in range(8):
        bitstring.append(0xff)

    for i in range(4):    ## black curtain
        bitstring.append(0x00)

    bitstring.append(0x00)

    bitstring.append(0x02) ## enhanced rle

    bitstring.append(0x01)

    for i in range(21):
        bitstring.append(0x00)



    n=0
    i=0
    j=0

    while i <1080:
        while j <1920:
            if i>0 and numpy.all(image[i,j,:]==image[i-1,j,:]):
                while j<1920 and numpy.all(image[i,j,:]==image[i-1,j,:]):
                    n=n+1
                    j=j+1

                bitstring.append(0x00)
                bitstring.append(0x01)
                bytecount+=2
                
                if n>=128:
                    byte1=(n & 0x7f)|0x80
                    byte2=(n >> 7)
                    bitstring.append(byte1)
                    bitstring.append(byte2)
                    bytecount+=2
                    
                else:
                    bitstring.append(n)
                    bytecount+=1
                n=0

            
            else:
                if j<1919 and numpy.all(image[i,j,:]==image[i,j+1,:]):
                    n=n+1
                    while j<1919 and numpy.all(image[i,j,:]==image[i,j+1,:]):
                        n=n+1
                        j=j+1
                    if n>=128:
                        byte1=(n & 0x7f)|0x80
                        byte2=(n >> 7)
                        bitstring.append(byte1)
                        bitstring.append(byte2)
                        bytecount+=2
                        
                    else:
                        bitstring.append(n)
                        bytecount+=1

                    bitstring.append(image[i,j-1,0])
                    bitstring.append(image[i,j-1,1])
                    bitstring.append(image[i,j-1,2])
                    bytecount+=3
                    
                    j=j+1
                    n=0

                else:
                    if j>1917 or numpy.all(image[i,j+1,:]==image[i,j+2,:]) or numpy.all(image[i,j+1,:]==image[i-1,j+1,:]):
                        bitstring.append(0x01)
                        bytecount+=1
                        bitstring.append(image[i,j,0])
                        bitstring.append(image[i,j,1])
                        bitstring.append(image[i,j,2])
                        bytecount+=3
                        
                        j=j+1
                        n=0

                    else:
                        bitstring.append(0x00)
                        bytecount+=1

                        toappend=[]

                        
                        while numpy.any(image[i,j,:]!=image[i,j+1,:]) and numpy.any(image[i,j,:]!=image[i-1,j,:]) and j<1919:
                            n=n+1
                            toappend.append(image[i,j,0])
                            toappend.append(image[i,j,1])
                            toappend.append(image[i,j,2])
                            j=j+1

                        if n>=128:
                            byte1=(n & 0x7f)|0x80
                            byte2=(n >> 7)
                            bitstring.append(byte1)
                            bitstring.append(byte2)
                            bytecount+=2
                                
                        else:
                            bitstring.append(n)
                            bytecount+=1

                        for k in toappend:
                            bitstring.append(k)
                            bytecount+=1
                        n=0
        j=0
        i=i+1
        bitstring.append(0x00)
        bitstring.append(0x00)
        bytecount+=2
    bitstring.append(0x00)
    bitstring.append(0x01)
    bitstring.append(0x00)
    bytecount+=3


    while (bytecount)%4!=0:
        bitstring.append(0x00)
        bytecount+=1        

    size=bytecount

    total=convlen(size,32)
    total=bitstobytes(total)
    for i in range(len(total)):
        bitstring[i+8]=total[i]    

    return bitstring, bytecount



##a dmd controller class

class dmd():
    def __init__(self):
        self.dev=usb.core.find(idVendor=0x0451 ,idProduct=0xc900 )

        self.dev.set_configuration()

        self.ans=[]

## standard usb command function

    def command(self,mode,sequencebyte,com1,com2,data=None):
        buffer = []

        flagstring=''
        if mode=='r':
            flagstring+='1'
        else:
            flagstring+='0'        
        flagstring+='1000000'
        buffer.append(bitstobytes(flagstring)[0])
        buffer.append(sequencebyte)
        temp=bitstobytes(convlen(len(data)+2,16))
        buffer.append(temp[0])
        buffer.append(temp[1])
        buffer.append(com2)
        buffer.append(com1)

        if len(buffer)+len(data)<65:
        
            for i in range(len(data)):
                buffer.append(data[i])

            for i in range(64-len(buffer)):
                buffer.append(0x00)


            self.dev.write(1, buffer)

        else:
            for i in range(64-len(buffer)):
                buffer.append(data[i])

            self.dev.write(1, buffer)

            buffer = []

            j=0
            while j<len(data)-58:
                buffer.append(data[j+58])
                j=j+1
                if j%64==0:
                    self.dev.write(1, buffer)

                    buffer = []

            if j%64!=0:

                while j%64!=0:
                    buffer.append(0x00)
                    j=j+1


                self.dev.write(1, buffer)                
                





        self.ans=self.dev.read(0x81,64)

## functions for checking error reports in the dlp answer

    def checkforerrors(self):
        self.command('r',0x22,0x01,0x00,[])
        if self.ans[6]!=0:
            print (self.ans[6])    

## function printing all of the dlp answer

    def readreply(self):
        for i in self.ans:
            print (hex(i))

## functions for idle mode activation

    def idle_on(self):
        self.command('w',0x00,0x02,0x01,[int('00000001',2)])
        self.checkforerrors()

    def idle_off(self):
        self.command('w',0x00,0x02,0x01,[int('00000000',2)])
        self.checkforerrors()

## functions for power management

    def standby(self):
        self.command('w',0x00,0x02,0x00,[int('00000001',2)])
        self.checkforerrors()

    def wakeup(self):
        self.command('w',0x00,0x02,0x00,[int('00000000',2)])
        self.checkforerrors()

    def reset(self):
        self.command('w',0x00,0x02,0x00,[int('00000010',2)])
        self.checkforerrors()

## test write and read operations, as reported in the dlpc900 programmer's guide

    def testread(self):
        self.command('r',0xff,0x11,0x00,[])
        self.readreply()

    def testwrite(self):
        self.command('w',0x22,0x11,0x00,[0xff,0x01,0xff,0x01,0xff,0x01])
        self.checkforerrors()

## some self explaining functions

    def changemode(self,mode):
        self.command('w',0x00,0x1a,0x1b,[mode])
        self.checkforerrors()

    def startsequence(self):
        self.command('w',0x00,0x1a,0x24,[2])
        self.checkforerrors()

    def pausesequence(self):
        self.command('w',0x00,0x1a,0x24,[1])
        self.checkforerrors()

    def stopsequence(self):
        self.command('w',0x00,0x1a,0x24,[0])
        self.checkforerrors()


    def configurelut(self,imgnum,repeatnum):
        img=convlen(imgnum,11)
        repeat=convlen(repeatnum,32)

        string=repeat+'00000'+img

        bytes=bitstobytes(string)

        self.command('w',0x00,0x1a,0x31,bytes)
        self.checkforerrors()
        

    def definepattern(self,index,exposure,bitdepth,color,triggerin,darktime,triggerout,patind,bitpos):
        payload=[]
        index=convlen(index,16)
        index=bitstobytes(index)
        for i in range(len(index)):
            payload.append(index[i])

        exposure=convlen(exposure,24)
        exposure=bitstobytes(exposure)
        for i in range(len(exposure)):
            payload.append(exposure[i])
        optionsbyte=''
        optionsbyte+='1'
        bitdepth=convlen(bitdepth-1,3)
        optionsbyte=bitdepth+optionsbyte
        optionsbyte=color+optionsbyte
        if triggerin:
            optionsbyte='1'+optionsbyte
        else:
            optionsbyte='0'+optionsbyte

        payload.append(bitstobytes(optionsbyte)[0])

        darktime=convlen(darktime,24)
        darktime=bitstobytes(darktime)
        for i in range(len(darktime)):
            payload.append(darktime[i])

        triggerout=convlen(triggerout,8)
        triggerout=bitstobytes(triggerout)
        payload.append(triggerout[0])

        patind=convlen(patind,11)
        bitpos=convlen(bitpos,5)
        lastbits=bitpos+patind
        lastbits=bitstobytes(lastbits)
        for i in range(len(lastbits)):
            payload.append(lastbits[i])



        self.command('w',0x00,0x1a,0x34,payload)
        self.checkforerrors()
        


    def setbmp(self,index,size):
        payload=[]

        index=convlen(index,5)
        index='0'*11+index
        index=bitstobytes(index)
        for i in range(len(index)):
            payload.append(index[i]) 


        total=convlen(size,32)
        total=bitstobytes(total)
        for i in range(len(total)):
            payload.append(total[i])         
        
        self.command('w',0x00,0x1a,0x2a,payload)
        self.checkforerrors()

## bmp loading function, divided in 56 bytes packages
## max  hid package size=64, flag bytes=4, usb command bytes=2
## size of package description bytes=2. 64-4-2-2=56

    def bmpload(self,image,size):

        packnum=size//504+1

        counter=0

        for i in range(packnum):
            if i %100==0:
                print (i,packnum)
            payload=[]
            if i<packnum-1:
                leng=convlen(504,16)
                bits=504
            else:
                leng=convlen(size%504,16)
                bits=size%504
            leng=bitstobytes(leng)
            for j in range(2):
                payload.append(leng[j])
            for j in range(bits):
                payload.append(image[counter])
                counter+=1
            self.command('w',0x11,0x1a,0x2b,payload)


            self.checkforerrors()


    def defsequence(self,images,exp,ti,dt,to,rep):

        self.stopsequence()

        arr=[]

        for i in images:
            arr.append(i)

##        arr.append(numpy.ones((1080,1920),dtype='uint8'))

        num=len(arr)

        encodedimages=[]
        sizes=[]

        for i in range((num-1)//24+1):
            print ('merging...')
            if i<((num-1)//24):
                imagedata=mergeimages(arr[i*24:(i+1)*24])
            else:
                imagedata=mergeimages(arr[i*24:])
            print ('encoding...')
            imagedata,size=encode(imagedata)

            encodedimages.append(imagedata)
            sizes.append(size)

            if i<((num-1)//24):
                for j in range(i*24,(i+1)*24):
                    self.definepattern(j,exp[j],1,'111',ti[j],dt[j],to[j],i,j-i*24)
            else:
                for j in range(i*24,num):
                    self.definepattern(j,exp[j],1,'111',ti[j],dt[j],to[j],i,j-i*24)

        self.configurelut(num,rep)

        for i in range((num-1)//24+1):
        
            self.setbmp((num-1)//24-i,sizes[(num-1)//24-i])

            print ('uploading...')
            self.bmpload(encodedimages[(num-1)//24-i],sizes[(num-1)//24-i])





