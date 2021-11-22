# Lutron Caseta Smartbridge Pro Python Plugin
#
# Author: Russell Weir
#

"""
<plugin key="CasetaPro" name="Caseta Smartbridge Pro" author="Russell Weir" version="1.0.0" externallink="https://github.com/Madrok/domoticz-plugin-contrib-caseta-smartbridge-pro">
    <description>
      <h2>Lutron Caseta Smartbridge Pro</h2><br/>
      This plugin allows Domoticz to connect to the Lutron Caseta system. Please note that
      only the Smartbridge PRO is supported.
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.1.100"/>
        <param field="Port" label="Port" width="100px" required="true" default="23"/>
        <param field="Mode1" label="Polling interval (seconds)" width="75px" required="true" default="30"/>

        <param field="Mode2" label="Observe changes" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>


        <param field="Mode3" label="Add groups as devices" width="75px">
            <options>
                <option label="Yes" value="True"/>
                <option label="No" value="False"  default="true" />
            </options>
        </param>

        <param field="Mode4" label="Integration Report" width="200px" required="true" />

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>

    </params>
</plugin>
"""
import Domoticz
import json
# import os


class BasePlugin:
    lights = {}
    connection = None
    nextConnect = 3
    connectStatus = "offline"
    queue = []

    def __init__(self):
        self.connectStatus = "offline"
        return

    def getDomoticzUnitNum(self, DeviceID):
        if len(Devices) > 0:
            for i in Devices:
                if Devices[i].DeviceID == DeviceID:
                    return i
        return -1

    def registerDevice(self, lutronDevice):
        Domoticz.Log("Registering: {0}".format(json.dumps(lutronDevice)))
        # Registering: {"Name": "Laundry Room", "Unit": -1, "DeviceID": 6}
        if lutronDevice["Unit"] != -1:
            i = lutronDevice["Unit"]
            self.lights[Devices[i].DeviceID] = \
                {"DeviceID": Devices[i].DeviceID, "Unit": i}
            return

        i = 1 if len(Devices) == 0 else max(Devices)+1

        # https://github.com/domoticz/domoticz/blob/development/hardware/plugins/PythonObjects.cpp ~line 465
        # PyDict_SetItemString(OptionsOut, "LevelActions", PyUnicode_FromString("|||"));
        # PyDict_SetItemString(OptionsOut, "LevelNames", PyUnicode_FromString("Off|Level1|Level2|Level3"));
        # PyDict_SetItemString(OptionsOut, "LevelOffHidden", PyUnicode_FromString("false"));
        # PyDict_SetItemString(OptionsOut, "SelectorStyle", PyUnicode_FromString("0"));
        options = {
            "LevelOffHidden": "false",
            "SelectorStyle": "0"}

        devID = lutronDevice['DeviceID']

        if not devID in self.lights:
            deviceType = 244  # hardware/hardwaretypes.h:#define pTypeGeneralSwitch 0xF4
            subType = 73  # hardware/hardwaretypes.h:#define sSwitchGeneralSwitch 0x49
            switchType = 7  # 0=non-dimmable, 9=push-on, 18=selector, defined in main/RFXNames.h

            # Basic device
            Domoticz.Device(Name=lutronDevice['Name'], Unit=i, Type=deviceType,
                            Subtype=subType, Switchtype=switchType, DeviceID=devID).Create()
            self.lights[devID] = {"DeviceID": devID, "Unit": i}

            # Domoticz.Device(Name=lutronDevice['Name'] + " - WB",  Unit=i, TypeName="Selector Switch", Switchtype=18, Options=WhiteOptions, DeviceID=devID+":WB").Create()
            # self.lights[devID+":WB"] = {"DeviceID": devID+":WB", "Unit": i}

    def updateDevice(self, dev):
        Domoticz.Log("updateDevice: {0}".format(json.dumps(dev)))
        devID = str(dev["DeviceID"])
        domUnit = self.lights[devID]['Unit']
        nVal = 1
        v = int((dev["Level"]/100)*100)
        if v == 0:
            # v = 1
            nVal = 0
        Domoticz.Log("ID: "+str(domUnit)+" v: "+str(v)+" nVal: "+str(nVal))
        Devices[domUnit].Update(nValue=nVal, sValue=str(v))

    def queueUpdates(self):
        if len(Devices) > 0:
            for i in Devices:
                if Devices[i].DeviceID in self.lights:
                    self.queue.append("?OUTPUT,"+Devices[i].DeviceID+",1")
                else:  # delete, since device is not in our integration report
                    Domoticz.log("Deleting Unit " + str(i))
                    Devices[i].Delete()
        if len(self.queue) > 0:
            self.connection.Send(self.queue.pop(0)+"\r\n")

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        Domoticz.Debug("onStart. Plugin home folder: " +
                       Parameters["HomeFolder"])

        Domoticz.Heartbeat(2)
        self.connectStatus = "offline"

        Domoticz.Debug(
            f"Trying to connect to {Parameters['Address']}:{Parameters['Port']}")
        try:
            self.connection = Domoticz.Connection(
                Name="Main", Transport="TCP/IP", Protocol="line", Address=Parameters["Address"], Port=Parameters["Port"])
        except:
            Domoticz.Error("Could not setup connection to Caseta Pro device")

        data = None
        try:
            Domoticz.Debug(f"Opening {Parameters['HomeFolder']}lutron.json")
            fp = open(Parameters["HomeFolder"] + "lutron.json")
            data = json.load(fp)
            fp.close()
            if not data:
                Domoticz.Error("Could not parse lutron.json data")
                return
        except:
            Domoticz.Error("Could not open lutron.json")

        try:
            data = data["LIPIdList"]
        except:
            Domoticz.Error("lutron.json missing 'LIPIdList'")
            return

        Domoticz.Log("Registering devices. "+str(len(Devices))+" exist ")
        for zone in data["Zones"]:
            zone["Name"] = zone["Name"] if zone["Name"] != "Lights" else zone["Area"]["Name"]
            zone["DeviceID"] = str(zone["ID"])
            zone.pop("ID", None)
            zone.pop("Area", None)
            zone["Unit"] = self.getDomoticzUnitNum(zone["DeviceID"])
            Domoticz.Log(
                "Found " + zone["Name"] + "(" + str(zone["DeviceID"]) + ") DomoticzID:" + str(zone["Unit"]))
            self.registerDevice(zone)

        try:
            self.connection.Connect()
        except:
            Domoticz.Error("Could not connect to Caseta Pro device")

    def onStop(self):
        # Domoticz.Log("onStop called")
        return True

    def onConnect(self, Connection, Status, Description):
        # Domoticz.Log("onConnect called")
        if (Status == 0):
            self.connectStatus = "login"
            Domoticz.Log("Connected successfully to: "+Parameters["Address"])
        else:
            self.connectStatus = "offline"
            Domoticz.Log("Failed to connect to Smartbridge. Status: {0} Description: {1}".format(
                Status, Description))
        return True

    def onMessage(self, Connection, Data):
        # Domoticz.Log("onMessage Received: " + str(Data))
        command = Data.decode("utf-8")
        if command == "login: ":
            Domoticz.Log("Sending login")
            Connection.Send("lutron\n")
            self.connectStatus = "password"
        elif command == "password: ":
            Domoticz.Log("Sending password")
            Connection.Send("integration\n")
            self.connectStatus = "await_prompt"
        elif command == "GNET> ":
            if self.connectStatus == "await_prompt":
                Domoticz.Log("Login successful")
                self.connectStatus = "connected"
                self.queueUpdates()
        else:
            if self.connectStatus == "connected":
                command = command.strip()
                parts = command.strip().split(",")
                # ~OUTPUT,2,1,0.00\r\n
                if parts[0] == "~OUTPUT":
                    dev = {
                        "DeviceID": parts[1]
                    }
                    if(parts[2] == "1"):
                        dev["Level"] = float(parts[3])
                        Domoticz.Log("Got level info from Lutron")
                        self.updateDevice(dev)
                    else:
                        Domoticz.Log("Ignoring command: " + command)
                elif parts[0] == "~DEVICE":
                    Domoticz.Log("Ignoring device: " + command)
                else:
                    Domoticz.Log("Unknown message: " + command)
                if len(self.queue) > 0:
                    self.connection.Send(self.queue.pop(0)+"\r\n")
            else:
                Domoticz.Error("message out of sync: " + command)
                self.connection.Close()

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Log("Command: " + str(Command)+" Level: "+str(Level)+" Type: "+str(Devices[Unit].Type)+" SubType: "+str(
            Devices[Unit].SubType)+" Color: "+str(Color) + " DeviceID: " + Devices[Unit].DeviceID)
        if str(Command) == "Off":
            self.connection.Send(
                "#OUTPUT,"+Devices[Unit].DeviceID+",1,0,00:03\r\n")
        else:
            # On command sent with a 0 level
            if Level == 0:
                Level = 100
            self.connection.Send(
                "#OUTPUT,"+Devices[Unit].DeviceID+",1,"+str(Level)+",00:03\r\n")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text +
                     "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        self.connectStatus = "offline"
        Domoticz.Log("Caseta Pro has disconnected")
        return

    def onHeartbeat(self):
        if (self.connection.Connected() == True):
            pass
        else:
            Domoticz.Log(
                "Not connected to Caseta Pro - nextConnect: {0}".format(self.nextConnect))
            self.nextConnect = self.nextConnect - 1
            if self.nextConnect <= 0:
                self.nextConnect = 3
                self.connection.Connect()


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
