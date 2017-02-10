##
### Writen by Eduardo J. (http://bms.mixmods.com.br/u7)
##

bl_info = {
    "name": "RenderWare 2D Effect Section Importer/Exporter for GTA",
    "author": "Eduardo J.",
    "version": (0, 0, 2),
    "blender": (2, 7, 8),
    "location": "Tools > GTA Tools > 2D Effects",
    "description": "Helper for Import/Export RenderWare 2D Effects Section for GTA",
    "category": "GTA Tools" }

import bpy
import struct
import math
import mathutils

###
### Informations Taken From: 
###    * http://www.gtamodding.com/wiki/2d_Effect_(RW_Section)
###    * http://www.gtamodding.com/wiki/Script.img#San_Andreas
###

coronaShowMode = (('0', "Default",                               "Default Show Mode"), 
                  ('1', "Random Flashing",                       "Light Is Random Flashing"),
                  ('2', "Random Flashing Always At Wet Weather", "Random Flashing Always At Wet Weather"),
                  ('3', "Lights Anim Speed 4x",                  "Used On Model 10 green bottles. Lights alternately switched on-off."),
                  ('4', "Lights Anim Speed 2x",                  "Used on skycrapers in San Fierro"),
                  ('5', "Lights Anim Speed 1x",                  "Lights Anim Speed 1x"),
                  ('6', "Unknown 1",                             "Unknown Value"),
                  ('7', "Traffic Light",                         "Traffic Light"),
                  ('8', "Train Cross Light",                     "Train Cross Light"),
                  ('9', "(Uknown) Always Disabled",              "(Unknown) Always Disabled"),
                  ('10', "At Rain Only",                         "Enables Only In Rainy Weather"),
                  ('11', "Flashing 5s 5s",                       "5s - ON, 5s - Off"),
                  ('12', "Flashing 6s 4s",                       "6s - ON, 4s - Off"),
                  ('13', "Flashing 6s 4s",                       "6s - ON, 4s - Off"))
                  
pedAttractorType = (('0', "PED_ATM_ATTRACTOR",            "Ped uses ATM (at day time only)"),
                    ('1', "PED_SEAT_ATTRACTOR",           "Ped sits (at day time only)"),
                    ('2', "PED_STOP_ATTRACTOR",           "Ped stands (at day time only)"),
                    ('3', "PED_PIZZA_ATTRACTOR",          "Ped stands for few seconds"),
                    ('4', "PED_SHELTER_ATTRACTOR",        "Ped goes away after spawning, but stands if weather is rainy"),
                    ('5', "PED_TRIGGER_SCRIPT_ATTRACTOR", "Launches an external script"),
                    ('6', "PED_LOOK_AT_ATTRACTOR",        "Ped looks at object, then goes away"),
                    ('8', "PED_PARK_ATTRACTOR",           "Ped lays (at day time only, ped goes away after 6 PM)"),
                    ('9', "PED_STEP_ATTRACTOR",           "Ped sits on steps"))

defaultExternalScripts = (('none',    "none",    "None Script"),
                          ('PCHAIR',  "PCHAIR",  "Restaurant ped in chair AI"),
                          ('TICKET',  "TICKET",  "Train ticket machine AI"),
                          ('SHOPPER', "SHOPPER", "Ped shopping AI"),
                          ('FBOOTHL', "FBOOTHL", "Ped eating food AI"),
                          ('FBOOTHR', "FBOOTHR", "Ped eating food AI"),
                          ('DANCER',  "DANCER",  "Club dancer AI"),
                          ('BARGUY',  "BARGUY",  "Barman AI"),
                          ('PEDSLOT', "PEDSLOT", "Slot-machine gamer AI"),
                          ('PEDCARD', "PEDCARD", "Card gamer AI"),
                          ('PEDROUL', "PEDROUL", "Roulette gamer AI"),
                          ('PRISONR', "PRISONR", "Prisoner AI"),
                          ('COPLOOK', "COPLOOK", "Inside police HQ cop looking at posters"),
                          ('BROWSE',  "BROWSE",  "Inside police HQ cop browsing folder or locker"))

roadSignUsedLines = (('0', "4 Lines", "Used 4 Lines"),
                     ('1', "1 Line",  "Used 1 Line"),
                     ('2', "2 Lines", "Used 2 Lines"),
                     ('3', "3 Lines", "Used 3 Lines"))

roadSignMaxSymbolsCount = (('0', "16 Symbols", "Max 16 Symbols per Line"),
                           ('1', "2 Symbols",  "Max 2 Symbols per Line"),
                           ('2', "4 Symbols",  "Max 4 Symbols per Line"),
                           ('3', "8 Symbols",  "Max 8 Symbols per Line"))

roadSignTextColor = (('0', "White", "Text is white"),
                     ('1', "Black", "Text is black"),
                     ('2', "Grey",  "Text is grey"),
                     ('3', "Red",   "Text is red"))
                  
def get2dfxExportables(context):
    exportables = []
    for object in context.selected_objects:
        parent = object.parent
        add = True
        
        while parent:
            if parent in context.selected_objects:
                add = False
                break
            parent = parent.parent
        if str(object.type) != "EMPTY":
            if str(object.type) != "MESH":
                add = False
        if object.use_2dfx_particle != True:
            if object.use_2dfx_light != True:
                if object.use_2dfx_ped_attractor != True:
                    if object.use_2dfx_roadsign != True:
                        add = False
        if add:
            exportables.append(object)
    return exportables

def packGtaString(writename, length):
    if len(writename) > length:
        writename = writename[:length]
    payload = struct.pack(str(len(writename)) + "s", bytearray(writename, "ascii"))
    num = length - len(writename)
    if num > 0:
        for x in range(0, num):
            payload += struct.pack("b", 0)
    return payload

def readGtaString(f, length):
    data = []
    nulled = False
    for i in range(0, length):
        if nulled == True:
            readFormat(f, "B")
        else:
            b = readFormat(f, "B")[0]
            byteA = b
            if b == 0:
                nulled = True
            else:
                data.append(byteA)
    return "".join(map(chr, data))

def readFormat(f, format):
    return struct.unpack(format, f.read(struct.calcsize(format)))

class Import2dEffectSection:
    class Rp2DEffectsEntryRoadSign:
        def __init__(self, index, x, y, z, size, f):
            self.index = index
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z
            data = readFormat(f, "fffff") #20
            self.size_x = data[0]
            self.size_y = data[1]
            self.rot_x = data[2]
            self.rot_y = data[3]
            self.rot_z = data[4]
            data = readFormat(f, "h") #2
            mask1 = 0x03
            mask2 = 0x08
            mask3 = 0x30
            self.usedLines = data[0] & mask1
            self.maxSymbols = data[0] & mask2
            self.textColor = data[0] & mask3
            print(data[0])
            self.line1 = readGtaString(f, 16) #16
            self.line2 = readGtaString(f, 16) #16
            self.line3 = readGtaString(f, 16) #16
            self.line4 = readGtaString(f, 16) #16
            readFormat(f, "h") #2

        def build(self):
            verts = [(-0.5,-0.5,-0.5),(-0.5,0.5,-0.5),(0.5,0.5,-0.5),(0.5,-0.5,-0.5)]
            faces = [(0,1,2,3)]
            
            me = bpy.data.meshes.new("roadsignMesh")
            obj = bpy.data.objects.new("roadsign " + str(self.index), me)
            me.from_pydata(verts,[],faces)
            
            obj.location = (self.pos_x, self.pos_y, self.pos_z)
            obj.rotation_mode = 'XYZ'
            obj.rotation_euler = (-math.radians(90 - self.rot_x), math.radians(self.rot_y), math.radians(self.rot_z))
            obj.dimensions = (self.size_y, self.size_x, 0.0)

            obj.roadsign_usedLines = str(self.usedLines)
            obj.roadsign_maxSymbols = str(self.maxSymbols)
            obj.roadsign_textColor = str(self.textColor)
            obj.roadsign_textLine1 = self.line1
            obj.roadsign_textLine2 = self.line2
            obj.roadsign_textLine3 = self.line3
            obj.roadsign_textLine4 = self.line4

            obj.use_2dfx_roadsign = True
            
            bpy.context.scene.objects.link(obj)

    class Rp2DEffectsEntryPedAttractor:
        def __init__(self, index, x, y, z, size, f):
            self.index = index
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z
            data = readFormat(f, "I")
            self.type = data[0]
            rot = readFormat(f, "fffffffff")
            rmatrix = mathutils.Matrix.Identity(3)
            rmatrix[0] = rot[0], rot[1], rot[2]
            rmatrix[1] = rot[3], rot[4], rot[5]
            rmatrix[2] = rot[6], rot[7], rot[8]
            rmatrix.resize_4x4()
            rmatrix.translation = x, y, z
            
            self.matrix = rmatrix
            
            self.scriptName = readGtaString(f, 8)
            data = readFormat(f, "I")
            self.probability = data[0]
            readFormat(f, "BBBB")
            
        def build(self):
            obj = bpy.data.objects.new("ped " + str(self.index), None)
            obj.matrix_local = self.matrix
                        
            obj.ped_attractor_type = str(self.type)
            obj.ped_external_script = self.scriptName
            obj.ped_existing_proability = self.probability
                        
            obj.use_2dfx_ped_attractor = True
            
            bpy.context.scene.objects.link(obj)
    
    class Rp2DEffectsEntryLight:
        def __init__(self, index, x, y, z, size, f):
            self.index = index
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z
            data = readFormat(f, "BBBB")
            intdata = data[0]
            self.colorRed = intdata
            intdata = data[1]
            self.colorGreen = intdata
            intdata = data[2]
            self.colorBlue = intdata
            intdata = data[3]
            self.colorAlpha = intdata
            data = readFormat(f, "ffff")
            self.distance = data[0]
            self.outerRange = data[1]
            self.size = data[2]
            self.innerRange = data[3]
            data = readFormat(f, "BBBBB")
            self.showMode = data[0]
            self.enableReflections = data[1]
            self.flareType = data[2]
            self.shadowMultiplier = data[3]
            self.flags1 = data[4]
            
            self.texture = str(readGtaString(f, 24))
            self.shadow = readGtaString(f, 24)
            data = readFormat(f, "BB")
            self.shadowZdistance = data[0]
            self.flags2  = data[1]
            if size == 76:
                readFormat(f, "B")
            else:
                readFormat(f, "BBBBB")
                
        def build(self):
            obj = bpy.data.objects.new("light " + str(self.index), None)
            obj.location.x = self.pos_x
            obj.location.y = self.pos_y
            obj.location.z = self.pos_z
            self.setFlags1(obj)
            self.setFlags2(obj)
            
            obj.light_color = (float(self.colorRed / 255.0), float(self.colorGreen / 255.0), float(self.colorBlue / 255.0))
            obj.light_color_alpha = self.colorAlpha
            obj.light_draw_distance = self.distance
            obj.light_size = self.size
            obj.light_inner_range = self.innerRange
            obj.light_outer_range = self.outerRange
            obj.light_texture = self.texture
            obj.light_shadow_texture = self.shadow
            obj.light_show_mode = str(self.showMode)
            if self.enableReflections == 0:
                obj.light_corona_enable_reflection = False
            else:
                obj.light_corona_enable_reflection = True
            obj.light_flare_type = self.flareType
            obj.light_shadow_multiplier = self.shadowMultiplier
            obj.light_shadow_zdistance = self.shadowZdistance
            
            obj.use_2dfx_light = True

            bpy.context.scene.objects.link(obj)
                
        def setFlags2(self, object):
            if self.flags2 & 1 == 1:
                object.light_flag2_corona_only_frombellow = True
            if self.flags2 & 2 == 2:
                object.light_flag2_blinking2 = True
            if self.flags2 & 4 == 4:
                object.light_flag2_update_height = True
            if self.flags2 & 8 == 8:
                object.light_flag2_checkdir = True
            if self.flags2 & 16 == 16:
                object.light_flag2_blinking3 = True
        
        def setFlags1(self, object):
            if self.flags1 & 1 == 1:
                object.light_flag1_corona_check_obstacles = True 
            if self.flags1 & 2 == 2:
                object.light_flag1_unkfog_type1 = True 
            if self.flags1 & 4 == 4:
                object.light_flag1_unkfog_type2 = True 
            if self.flags1 & 8 == 8:
                object.light_flag1_without_corona = True 
            if self.flags1 & 16 == 16:
                object.light_flag1_corona_only_at_long = True 
            if self.flags1 & 32 == 32:
                object.light_flag1_at_day = True 
            if self.flags1 & 64 == 64:
                object.light_flag1_at_night = True 
            if self.flags1 & 128 == 128:
                object.light_flag1_blinking = True
            
    class Rp2DEffectsEntryParticle:
        def __init__(self, index, x, y, z, size, f):
            self.index = index
            self.pos_x = x
            self.pos_y = y
            self.pos_z = z
            self.name = readGtaString(f, 24)
            
        def build(self):
            obj = bpy.data.objects.new("particle " + str(self.index), None)
            obj.location.x = self.pos_x
            obj.location.y = self.pos_y
            obj.location.z = self.pos_z
            
            obj.use_2dfx_particle = True
            obj.particle_name = self.name
            
    def __init__(self, filepath):
        self.particles = []
        self.lights = []
        self.peds = []
        self.roadSigns = []
        self.count = 0
        self.f = open(filepath, "rb")
        self.read()
        self.f.close()  
    
    def read(self):
        data = readFormat(self.f, "I")
        self.count = data[0]
        lIndex = 0
        pIndex = 0
        pedIndex = 0
        roadSignIndex = 0
        for i in range(0, self.count):
            data = readFormat(self.f, "fffII")
            pos_x = data[0]
            pos_y = data[1]
            pos_z = data[2]
            type = data[3]
            size = data[4]
            if (type == 0):
                l = self.Rp2DEffectsEntryLight(lIndex, pos_x, pos_y, pos_z, size, self.f)
                lIndex += 1
                self.lights.append(l)
            elif (type == 1):
                p = self.Rp2DEffectsEntryParticle(pIndex, pos_x, pos_y, pos_z, size, self.f)
                pIndex += 1
                self.particles.append(p)
            elif (type == 3):
                p = self.Rp2DEffectsEntryPedAttractor(pedIndex, pos_x, pos_y, pos_z, size, self.f)
                pedIndex += 1
                self.peds.append(p)
            elif (type == 7):
                rd = self.Rp2DEffectsEntryRoadSign(roadSignIndex, pos_x, pos_y, pos_z, size, self.f)
                roadSignIndex += 1
                self.roadSigns.append(rd)
            else:
                curPos = self.f.tell()
                self.f.seek(curPos + size)
    
    def build(self):
        for l in self.lights:
            l.build()
        for p in self.particles:
            p.build()
        for p in self.peds:
            p.build()
        for rd in self.roadSigns:
            rd.build()

class Export2dEffectSection:
    class Rp2DEffectsEntryRoadSign:
        def __init__(self, obj):
            self.pos_x = obj.location.x
            self.pos_y = obj.location.y
            self.pos_z = obj.location.z
            obj.rotation_mode = 'XYZ'
            self.rot_x = math.degrees(obj.rotation_euler.x) + 90
            self.rot_y = math.degrees(obj.rotation_euler.y)
            self.rot_z = math.degrees(obj.rotation_euler.z)
            
            self.size_y = obj.dimensions.x
            self.size_x = obj.dimensions.y
            
            self.usedLines = int(obj.roadsign_usedLines)
            self.maxSymbols = int(obj.roadsign_maxSymbols)
            self.textColor = int(obj.roadsign_textColor)
            
            self.line1 = obj.roadsign_textLine1
            self.line2 = obj.roadsign_textLine2
            self.line3 = obj.roadsign_textLine3
            self.line4 = obj.roadsign_textLine4
            
            self.flags = 0
            self.flags |= self.usedLines
            self.flags |= self.maxSymbols << 2
            self.flags |= self.textColor << 4
            
        def binString(self, mstr):
            if len(mstr) > 16:
                mstr = writename[:16]
            payload = struct.pack(str(len(mstr)) + "s", bytearray(mstr, "ascii"))
            num = 16 - len(mstr)
            if num > 0:
                for x in range(0, num):
                    payload += struct.pack("b", 0x5f)
            return payload
            
        def bin(self):
            datasize = 88
            payload = struct.pack("fffII", self.pos_x, self.pos_y, self.pos_z, 7, datasize)
            payload += struct.pack("fffff", self.size_x, self.size_y, self.rot_x, self.rot_y, self.rot_z)
            payload += struct.pack("h", self.flags)
            payload += self.binString(self.line1)
            payload += self.binString(self.line2)
            payload += self.binString(self.line3)
            payload += self.binString(self.line4)
            payload += struct.pack("h", 7994)
            return payload
    
    class Rp2DEffectsEntryPedAttractor:
        class RwRotMatrix:
            def __init__(self):
                self.m = [1, 0, 0, 0, 1, 0, 0, 0, 1]
                
            def bin(self):
                return struct.pack("9f", *self.m)
            
        def __init__(self, obj):
            self.type = int(obj.ped_attractor_type)
            self.scriptName = obj.ped_external_script
            self.probability = obj.ped_existing_proability
            
            self.rotation = self.RwRotMatrix()
            ux = obj.matrix_local.to_3x3()
            self.rotation.m = [ux[0][0], ux[0][1], ux[0][2], ux[1][0], ux[1][1], ux[1][2], ux[2][0], ux[2][1], ux[2][2]]
            self.pos_x = obj.matrix_local.translation[0]
            self.pos_y = obj.matrix_local.translation[1]
            self.pos_z = obj.matrix_local.translation[2]
            
        def bin(self):
            datasize = 56
            payload = struct.pack("fffII", self.pos_x, self.pos_y, self.pos_z, 3, datasize)
            payload += struct.pack("I", self.type)
            payload += self.rotation.bin()
            #40
            payload += packGtaString(self.scriptName, 8)
            #8
            payload += struct.pack("I", self.probability)
            #4
            payload += struct.pack("BBBB", 0, 0, 0, 0)
            #4
            return payload
                
    class Rp2DEffectsEntryLight:
        def __init__(self, object):
            self.colorRed = math.ceil(object.light_color.r * 255)
            self.colorGreen = math.ceil(object.light_color.g * 255)
            self.colorBlue = math.ceil(object.light_color.b * 255)
            self.colorAlpha = object.light_color_alpha
            self.distance = object.light_draw_distance
            self.size = object.light_size
            self.innerRange = object.light_inner_range
            self.outerRange = object.light_outer_range
            self.texture = object.light_texture
            self.shadow = object.light_shadow_texture
            self.showMode = int(object.light_show_mode)
            if object.light_corona_enable_reflection == True:
                self.enableReflections = 1
            else:
                self.enableReflections = 0
            self.flareType = object.light_flare_type
            self.shadowMultiplier = object.light_shadow_multiplier
            self.shadowZdistance = object.light_shadow_zdistance
            self.pos_x = object.location.x
            self.pos_y = object.location.y
            self.pos_z = object.location.z
            self.flags1 = self.getFlags1(object)
            self.flags2 = self.getFlags2(object)
                    
        def getFlags2(self, object):
            flags = 0
            if object.light_flag2_corona_only_frombellow == True:
                flags = flags | 1
            if object.light_flag2_blinking2 == True:
                flags = flags | 2           
            if object.light_flag2_update_height == True:
                flags = flags | 4           
            if object.light_flag2_checkdir == True:
                flags = flags | 8           
            if object.light_flag2_blinking3 == True:
                flags = flags | 16                  
            return flags
                        
        def getFlags1(self, object):
            flags = 0
            if object.light_flag1_corona_check_obstacles == True:
                flags = flags | 1
            if object.light_flag1_unkfog_type1 == True:
                flags = flags | 2
            if object.light_flag1_unkfog_type2 == True:
                flags = flags | 4
            if object.light_flag1_without_corona == True:
                flags = flags | 8
            if object.light_flag1_corona_only_at_long == True:
                flags = flags | 16
            if object.light_flag1_at_day == True:
                flags = flags | 32
            if object.light_flag1_at_night == True:
                flags = flags | 64
            if object.light_flag1_blinking == True:
                flags = flags | 128
            return flags
            
        def bin(self):
            datasize = 76
            payload = struct.pack("fffII", self.pos_x, self.pos_y, self.pos_z, 0, datasize)
            payload += struct.pack("BBBB", self.colorRed, self.colorGreen, self.colorBlue, self.colorAlpha)
            # 4
            payload += struct.pack("ffff", self.distance, self.outerRange, self.size, self.innerRange)
            # 16
            payload += struct.pack("BB", self.showMode, self.enableReflections)
            payload += struct.pack("BBB", self.flareType, self.shadowMultiplier, self.flags1)
            # 5
            payload += packGtaString(self.texture, 24)
            payload += packGtaString(self.shadow, 24)
            # 48
            payload += struct.pack("BBB", self.shadowZdistance, self.flags2, 0)
            # 3
            return payload

    class Rp2DEffectsEntryParticle:
        def __init__(self, object):
            self.particleName = object.particle_name
            self.pos_x = object.location.x
            self.pos_y = object.location.y
            self.pos_z = object.location.z
            
        def bin(self):
            payload = struct.pack("fffII", self.pos_x, self.pos_y, self.pos_z, 1, 24)
            payload += packGtaString(self.particleName, 24)
            return payload
        
    def __init__(self, context):
        objects = get2dfxExportables(context)
        self.particles = []
        self.lights = []
        self.peds = []
        self.roadSigns = []
        for obj in objects:
            if obj.use_2dfx_particle == True:
                l = self.Rp2DEffectsEntryParticle(obj)
                self.particles.append(l)
            if obj.use_2dfx_light == True:
                # Light
                l = self.Rp2DEffectsEntryLight(obj)
                self.lights.append(l)
            if obj.use_2dfx_ped_attractor == True:
                p = self.Rp2DEffectsEntryPedAttractor(obj)
                self.peds.append(p)
            if obj.use_2dfx_roadsign == True:
                sign = self.Rp2DEffectsEntryRoadSign(obj)
                self.roadSigns.append(sign)
        
    def bin(self):
        count = len(self.particles)
        count += len(self.lights)
        count += len(self.peds)
        count += len(self.roadSigns)
        print(count)
        payload = struct.pack("I", count)
        for l in self.lights:
            payload += l.bin()
        for p in self.particles:
            payload += p.bin()
        for p in self.peds:
            payload += p.bin()
        for p in self.roadSigns:
            payload += p.bin()
        return payload

from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty, IntProperty
from bpy.types import Operator

class Effects2DImporter(Operator, ImportHelper):
    bl_idname = "import.effects2d"
    bl_label = "Import 2D Effects"
    filename_ext = ".sec"
    
    filter_glob = StringProperty(
            default="*.sec",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
            
    def execute(self, context):
        importer = Import2dEffectSection(self.filepath)
        importer.build()
        return {'FINISHED'}

class Effects2DExporter(Operator, ExportHelper):
    bl_idname = "export.effects2d"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export 2D Effects"
    filename_ext = ".sec"
    
    filter_glob = StringProperty(
            default="*.sec",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )
    
    def execute(self, context):
        exporter = Export2dEffectSection(context)
        f = open(self.filepath, 'wb')
        f.write(exporter.bin())
        f.close()
        return {'FINISHED'}
    
class UI_Effect2DExporter(bpy.types.Panel):
    bl_idname = "GTA_TOOLS_PANEL_EFF2D"
    bl_label = "2D Effects"
    bl_category = "GTA Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label("Current Support: ")
        box.label("  -Particles")
        box.label("  -Lights")
        box.label("  -Peds")
        box.label("  -Street Sign")
        layout.operator("import.effects2d", text="Import")
        layout.operator("export.effects2d", text="Export")

class UI_PropPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}    
    
    @classmethod
    def poll(cls, context):
        if(context.object is not None):
            return str(context.object.type) == "EMPTY"
        else:
            return False

class UI_Effects2DPedAttractorPanel(UI_PropPanel, bpy.types.Panel):
    bl_idname = "GTA_TOOLS_EFFECT_PEDATT"
    bl_label = "2DFX: Ped Attractor"

    global default_external_script
    
    bpy.types.Object.use_2dfx_ped_attractor = BoolProperty(name = "Using2DFXPedAttractor")
    bpy.types.Object.ped_attractor_type = EnumProperty(name="Type",
                                                items = pedAttractorType,
                                                default = '3',
                                                description = "Ped Attractor Type")
    bpy.types.Object.ped_external_script = EnumProperty(name="External Script Name",
                                                default = "none",
                                                items = defaultExternalScripts,
                                                description = "External Script Name")
    bpy.types.Object.ped_existing_proability = IntProperty(name="Probability",
                                                default = 50,
                                                min = 0,
                                                max = 100,
                                                description = "Ped Existing Probability")
    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "use_2dfx_ped_attractor", text="")
        
    def draw(self, context):
        layout = self.layout
        obj = context.object

        layout.prop(obj, "ped_attractor_type")
        layout.prop(obj, "ped_external_script")
        layout.prop(obj, "ped_existing_proability")

class UI_Effect2DLightPanel(UI_PropPanel, bpy.types.Panel):
    bl_idname = "GTA_TOOLS_EFFECT_LIGHT"
    bl_label = "2DFX: Light"
    ###
    ### 2DfX: Light Properties ###
    ##3
    bpy.types.Object.use_2dfx_light = BoolProperty(name = "Using2DFXLight")
    bpy.types.Object.light_color = FloatVectorProperty(
                                            name = "Color",
                                            subtype = 'COLOR_GAMMA',
                                            default = (1.0, 1.0, 1.0),
                                            min = 0.0,
                                            max = 1.0,
                                            description = "Light Color")
    bpy.types.Object.light_color_alpha = IntProperty(
                                            name = "Color Alpha",
                                            default = 255,
                                            min = 0,
                                            max = 255,
                                            description = "Color Transparency")
    bpy.types.Object.light_draw_distance = FloatProperty(
                                            name = "Distance",
                                            min = 0.0,
                                            max = 300.0,
                                            default = 100.0,
                                            description = "Light Draw Distance")
    bpy.types.Object.light_size = FloatProperty(
                                            name = "Size",
                                            min = 0.0,
                                            max = 300.0,
                                            default = 12.0,
                                            description = "Light Size")
    bpy.types.Object.light_inner_range = FloatProperty(
                                            name = "Inner Range",
                                            min = 0.0,
                                            max = 300.0,
                                            default = 2.0,
                                            description = "Light Inner Range")
    bpy.types.Object.light_outer_range = FloatProperty(
                                            name = "Outer Range",
                                            min = 0.0,
                                            max = 300.0,
                                            default = 8.0,
                                            description = "Light Outer Range")
    bpy.types.Object.light_texture = StringProperty(
                                            name = "Texture",
                                            default = "coronastar",
                                            description = "Light Corona Texture")
    bpy.types.Object.light_shadow_texture = StringProperty(
                                            name = "Shadow Texture",
                                            default = "shad_exp",
                                            description = "Corona Shadow Texture")
    bpy.types.Object.light_show_mode = EnumProperty(name = "Show Mode",
                                            default = '0',
                                            items = coronaShowMode,
                                            description = "Corona Show Mode")
    bpy.types.Object.light_corona_enable_reflection = BoolProperty(name = "Reflection",
                                            default = True,
                                            description = "Enable Corona Reflection")
    bpy.types.Object.light_flare_type = IntProperty(name = "Flare Type",
                                            min = 0,
                                            max = 255,
                                            default = 0,
                                            description = "Corona Flare Type")
    bpy.types.Object.light_shadow_multiplier = IntProperty(name = "Shadow Multiplier",
                                            min = 0,
                                            max = 255,
                                            default = 80,
                                            description = "Shadow Color Multiplier")
    bpy.types.Object.light_shadow_zdistance = IntProperty(name = "Shadow Z Distance",
                                            min = 0,
                                            max = 255,
                                            default = 0,
                                            description = "Shadow Z Distance")   
    ###
    ### Flags 1 ###
    ##3
    bpy.types.Object.light_flag1_corona_check_obstacles = BoolProperty(name = "Corona Check Obstacles",
                                            default = False,
                                            description = "Corona Check Obstacles")
    bpy.types.Object.light_flag1_unkfog_type1 = BoolProperty(name = "(Unknown)Fog Type",
                                            default = False,
                                            description = "Fog Type")
    bpy.types.Object.light_flag1_unkfog_type2 = BoolProperty(name = "(Unknown)Fog Type",
                                            default = False,
                                            description = "Fog Type")
    bpy.types.Object.light_flag1_without_corona = BoolProperty(name = "Without Corona",
                                            default = False,
                                            description = "Without Corona")
    bpy.types.Object.light_flag1_corona_only_at_long = BoolProperty(name = "Corona Only At Long Distance",
                                            default = False,
                                            description = "Corona Only At Long Distance")
    bpy.types.Object.light_flag1_at_day = BoolProperty(name = "At Day",
                                            default = False,
                                            description = "At Day")
    bpy.types.Object.light_flag1_at_night = BoolProperty(name = "At Night",
                                            default = False,
                                            description = "At Night")
    bpy.types.Object.light_flag1_blinking = BoolProperty(name = "Blinking1",
                                            default = False,
                                            description = "Blinking1") 
    ###
    ### Flags 2 ###
    ##3
    bpy.types.Object.light_flag2_corona_only_frombellow = BoolProperty(name = "Corona Only From Bellow",
                                            default = False,
                                            description = "Corona Only From Bellow")
    bpy.types.Object.light_flag2_blinking2 = BoolProperty(name = "Blinking2",
                                            default = False,
                                            description = "Blinking2")
    bpy.types.Object.light_flag2_update_height = BoolProperty(name = "Update Height Above Ground",
                                            default = False,
                                            description = "Update Height Above Ground")
    bpy.types.Object.light_flag2_checkdir = BoolProperty(name = "Check Direction",
                                            default = False,
                                            description = "Check Direction")
    bpy.types.Object.light_flag2_blinking3 = BoolProperty(name = "Blinking3",
                                            default = False,
                                            description = "Blinking3")
    
    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "use_2dfx_light", text="")
        
    def draw(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "light_color")
        layout.prop(obj, "light_color_alpha")
        layout.prop(obj, "light_draw_distance")    
        layout.prop(obj, "light_size")    
        layout.prop(obj, "light_inner_range")
        layout.prop(obj, "light_outer_range")
        layout.prop(obj, "light_show_mode")
        layout.prop(obj, "light_corona_enable_reflection")
        layout.prop(obj, "light_flare_type")
        layout.prop(obj, "light_shadow_multiplier")
        
        box = layout.box()
        box.label("Flags 1")
        box.prop(obj, "light_flag1_corona_check_obstacles")
        box.prop(obj, "light_flag1_unkfog_type1")
        box.prop(obj, "light_flag1_unkfog_type2")
        box.prop(obj, "light_flag1_without_corona")
        box.prop(obj, "light_flag1_corona_only_at_long")
        box.prop(obj, "light_flag1_at_day")
        box.prop(obj, "light_flag1_at_night")
        box.prop(obj, "light_flag1_blinking")        
        
        layout.prop(obj, "light_texture")
        layout.prop(obj, "light_shadow_texture")
        layout.prop(obj, "light_shadow_zdistance")
        
        box = layout.box()
        box.label("Flags 2")
        box.prop(obj, "light_flag2_corona_only_frombellow")
        box.prop(obj, "light_flag2_blinking2")
        box.prop(obj, "light_flag2_update_height")
        box.prop(obj, "light_flag2_checkdir")
        box.prop(obj, "light_flag2_blinking3")
        

class UI_Effect2DParticlePanel(UI_PropPanel, bpy.types.Panel):
    bl_idname = "GTA_TOOLS_EFFECT_PARTICLE"
    bl_label = "2DFX: Particle"
    bpy.types.Object.use_2dfx_particle = bpy.props.BoolProperty(name = "Using2DFXParticle")
    bpy.types.Object.particle_name = bpy.props.StringProperty(name="Particle Name")

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "use_2dfx_particle", text="")

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj, "particle_name")

class UI_Effect2DRoadSignPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}    
    bl_idname = "GTA_TOOLS_EFFECT_ROADSIGN"
    bl_label = "2DFX: Road Sign"
    bpy.types.Object.use_2dfx_roadsign = BoolProperty(name = "Using2DFXRoadSign")
    bpy.types.Object.roadsign_usedLines = EnumProperty(name = "Used Lines",
                                                default = '0',
                                                items = roadSignUsedLines,
                                                description = "Used Lines Flag")
    bpy.types.Object.roadsign_maxSymbols = EnumProperty(name = "Max Symbols",
                                                default = '0',
                                                items = roadSignMaxSymbolsCount,
                                                description = "Max Symbols per Line Flag")
    bpy.types.Object.roadsign_textColor = EnumProperty(name = "Text Color",
                                                default = '0',
                                                items = roadSignTextColor,
                                                description = "Text Color Flag")
    bpy.types.Object.roadsign_textLine1 = StringProperty(name = "Line 1",
                                                description = "The Text Line 1",
                                                maxlen = 16)
    bpy.types.Object.roadsign_textLine2 = StringProperty(name = "Line 2",
                                                description = "The Text Line 2",
                                                maxlen = 16)
    bpy.types.Object.roadsign_textLine3 = StringProperty(name = "Line 3",
                                                description = "The Text Line 3",
                                                maxlen = 16)
    bpy.types.Object.roadsign_textLine4 = StringProperty(name = "Line 4",
                                                description = "The Text Line 4",
                                                maxlen = 16)
    @classmethod
    def poll(cls, context):
        if(context.object is not None):
            return str(context.object.type) == "MESH"
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "use_2dfx_roadsign", text="")

    def draw(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj, "roadsign_usedLines")
        layout.prop(obj, "roadsign_maxSymbols")
        layout.prop(obj, "roadsign_textColor")
        box = layout.box()
        box.label("Text:")
        box.prop(obj, "roadsign_textLine1")
        box.prop(obj, "roadsign_textLine2")
        box.prop(obj, "roadsign_textLine3")
        box.prop(obj, "roadsign_textLine4")

def register():
    bpy.utils.register_module(__name__)
    
def unregister():
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    unregister()
    register()