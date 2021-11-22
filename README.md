# domoticz-plugin-contrib-caseta-smartbridge-pro
A plugin for Lutron Caseta Smartbridge Pro for the Domoticz home automation system


# Setup
Go into your domoticz/plugins folder and git clone this repository.

To use this plugin, telnet support needs to be activated on the Smartbridge Pro,
an Integration Report needs to be generated, and the bridge must have a static IP address. 
All of these can be found in Settings->Advanced->Integration. 

Once you have downloaded an integration report, place that file in this plugin's directory
and name it 'lutron.json'.

## Add hardware device
Domoticz->Hardware
Select type "Caseta Smartbridge Pro", give it a name, and I recommend specifying a Data Timeout.
Set the bridge's IP address, with the default telnet port 23, polling interval 15, Observe Changes
and 'Add groups as devices' as Yes. Lastly, type in the name of the integration report file.

## Add the discovered devices
Go into Setup->Devices to add the individual light switches you want to use with Domoticz

## To Do
* Make Integration Report a field so that we don't have to create the lutron.json file.
* Register new devices automatically. Right now they are ignored if they are not in the integration report

