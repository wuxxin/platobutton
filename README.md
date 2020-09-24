# PlatoButton

Implements in software what the headset hardware is missing:

+ Buttons to select mode, time, power, start and stop
+ Offline mode (no internet access, mobile phone, gps location required)

## Usage

./platobutton.py [-d <device>] [-m <mode>] [-t <minutes>] [-p <mikroampere>]

Press "s" to stop, "+" to increase and "-" to decrease powerlevel

## build requirements

+ https://github.com/labapart/gattlib
```
sudo apt install libbluetooth-dev libreadline-dev
git clone https://github.com/labapart/gattlib.git
cd gattlib
mkdir build
cd build
cmake -D ..
make
sudo make install
```

## Protocol

+ Presetup / Discovery
    + plato_service = "e8f22220-9796-42a1-92ef-f65a7f9d6d79"

+ Loop
    + Write Command
        + plato_write_uuid = "e8f20002-9796-42a1-92ef-f65a7f9d6d79"
        + (G)ATT Write Request (0x12), Handle: 0x0014
        + (G)ATT Write Response (0x13), Handle: 0x0014
    + Read Command Response
        + plato_read_uuid = "e8f20001-9796-42a1-92ef-f65a7f9d6d79"
        + (G)ATT Read Request (0x0a), Handle: 0x0011
        + (G)ATT Read Response (0x0b), Handle: 0x0011

### Commands

+ "F": Get Firmware Version
    + Write "F"
    + Read "1,v31"+ Binarybyte (00) ?
    + or sometimes after usage and stop Read "7,v31"

+ "#": Get Headset Serial
    + Write "#"
    + Read "#,01234567 89ABCDEF"
      + F1: 4 Bytes Hexadecimal: Serial ?
      + F2: 4 Bytes Hexadecimal: Last 4 Bytes of BLE Adress

+ "0/0": Get Status (usually once per second)
    + Write "0/0"
    + read "1,0000,408,000,0000"
    + eq."F1:1-7,F2:0000-1800,F3:400-408,F4:000-140,F5:0000-1300"

      + F1: Activity State (1-7)
        + 1: Idle
        + 2: Acknowledge Programstart
        + 3: ? Unseen ?
        + 4: Measuring Conectivity ?
        + 5: Active
        + 6: Stopping
        + 7: Stopped
      + F2: seconds of Device or Mode usage
      + F3: Battery status (040 ~ near full, less = less full)
      + F4: Output Powerlevel (1 unit = 10 mikroampere)
      + F5: Measured Something (1 unit = 1 mikroampere ?)

+ "4,[RLB],[RLB],[0-9]{3},[0-9]{4}/0": Start Programm
    + Write "4,R,L,040,1800/0"
      + F1: 4=Start Program
      + F2: R,L,B = Kathode/Donator Operating Mode
      + F3: R,L,B = Anode/Akzeptor Operating Mode
      + Operating modes (F2,F3)
        + Create: R -> L
        + Rethink: B -> L
        + Learn: L -> R
        + Concentrate: L -> B
      + F4: Always "040" ?
      + F5: Duration of program in seconds, 1800s=30minutes
      + F6: Always "/0" = Send Status Back ?

+ "5,(080|120|160)": Change Powerlevel (1 unit= 10 Mikroampere)
    + Write "5,080" = 0.8 Milliampere = 800 Mikroampere
    + Write "5,120" = 1.2 Milliampere = 1200 Mikroampere
    + Write "5,160" = 1.6 Milliampere = 1600 Mikroampere

+ "6/0": Stop Programm
    + Write "6/0"

#### Unknown Commands

+ seen,   unsure:  Write "A": Abort /Suspend ? Program
+ unseen, missing: Write "1"
+ seen,   unknown: Write "2"
+ unseen, missing: Write "3"

### Protocol Dump

+ Write
    + plato_write_uuid = "e8f20002-9796-42a1-92ef-f65a7f9d6d79"
    + (G)ATT Write Request (0x12), Handle: 0x0014
    + (G)ATT Write Response (0x13), Handle: 0x0014
    + Observed Value List
```
"F"
"#"
"0/0"
"4,R,L,040,1800/0"
"4,R,L,040,1763/0"
"5,120"
"5,160"
"5,080"
"6/0"
"A"
"2"
```

+ Read
    + plato_read_uuid = "e8f20001-9796-42a1-92ef-f65a7f9d6d79"
    + (G)ATT Read Request (0x0a), Handle: 0x0011
    + (G)ATT Read Response (0x0b), Handle: 0x0011
    + Observed Example Value List
```
"1,v31"+ 00
"#,01234567 89ABCDEF"
"1,0000,408,000,0000"
"2,0000,408,001,0015"
"4,0008,406,042,0455"
"5,0004,406,042,0463"
"6,0040,405,017,0276"
"6,0036,406,002,0190"
"7,0037,407,000,0000"
"7,0008,408,000,0000"
```

+ Example Session 1
  + W: "4,L,R,040,1800/0"
  + R: 2,053,404,001,0015
  + W: "0/0" once per second
  + R: 4,077,403,001,0109
    + 01,132 16,296 30,381
  + R: 5,080,403,042,432

+ Example Session 2
  + W: "4,L,B,040,1800/0"
  + R: 2,000,406,001,0007
  + W: "0/0" once per second
  + R: 4,000,403,001,0046
  + R: 4,001,403,016,0420
  + R: 4,002,403,030,0697
  + R: 5,003,403,042,0849
  + R: 5,004,403,042,0822
  + R: 5,005,403,042,0814
  + Loop
    + W: "0/0"
    + R: 5,Increase of 1, ~403, ~042, ~ 700-850
  + W: "5,060"
  + R: "4,0012,403,042,0701"
  + W: "0/0"
  + R: "4,0012,404,042,0693"
  + W: "5,060"
  + R: "4,0013,404,057,0830"
  + W: "0/0"
  + R: "4,0013,404,057,0826"
  + Loop
    + W: "0/0"
    + R: "4,0013-0017,402-404,057-115,0826 - 1251
  + Loop
    + W: "0/0"
    + R: "5,0018-0030,402,122-142,1024-1227"
  + W: "6/0"
  + R: "6,0042,402,142,1114"
  + W: "0/0"
  + R: "6,0043,402,142,1118"
  + R: "6,time,402,decreasing in steps of ~20,decreasing in steps of ~100"
  + 113,958 99,884 84,802 70,720 55,627 41,537 26,432 11,315
  + R: "7, 0053, 405, 000,0000"
