# kagi

*A RFID based key box*


## Get started

### Features

- MFRC522 card support
- Passcode requirement
- Logging capabilities


### Prerequisites

#### Hardware

- Raspberry pi
- MFRC522 compatible RFID reader
- Numpad keyboard
- GPIO compatible LED light
- GPIO compatible speaker


### Software

- Python 3.10+
- Postgresql database
- Internet connection (duh)
- SSH (recommended)


### Setup

#### Connecting the parts



### Database



### Software



## Security



### Attack surface



### Undefined behaviour - Data races



## Privacy

**What information is stored?**

- Logs every card read locally
    - This includes the current time of day, your card id and the status of your card reading. This status can be whether or not you were granted access and why.
- Stores your card id, passcode (salted, peppered and hashed) and optionally your name in the database.
    - This database may be located on another machine.
    - Note that your name is manually entered by human person into the database.


## 3D printed box



