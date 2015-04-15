#------------------------------------------------------------------------------
# Name:        rc.py
# Purpose:     Resource Compiler Transactions
#
# Author:      N/A
#
# Created:     N/A
# Copyright:   (c) N/A
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


if 'bpy' in locals():
    import imp
    imp.reload(utils)
else:
    import bpy
    from io_export_cryblend import utils

from io_export_cryblend.outPipe import cbPrint
from io_export_cryblend.utils import Path
from xml.dom.minidom import Document, parseString
import fnmatch
import os
import shutil
import subprocess
import threading
import tempfile


class RCInstance:

    def __init__(self, config):
        self.__config = config

    def convert_tif(self, source):
        if not self.__config.do_textures:
            return

        converter = _TIFConverter(self.__config, source)
        conversion_thread = threading.Thread(target=converter)
        conversion_thread.start()

    def convert_dae(self, source):
        converter = _DAEConverter(self.__config, source)
        conversion_thread = threading.Thread(target=converter)
        conversion_thread.start()


class _DAEConverter:

    def __init__(self, config, source):
        self.__config = config
        self.__doc = source

    def __call__(self):
        dae_path = Path(self.__config.filepath)
        dae_path.generate_file(self.__doc)

        dae_path = utils.get_absolute_path_for_rc(dae_path)

        if not self.__config.disable_rc:
            rc_params = [
                '/verbose',
                '/threads=processors',
                '/refresh']
            if self.__config.do_materials:
                rc_params.append('/createmtl=1')

            rc_process = run_rc(self.__config.rc_path, dae_path, rc_params)

            if rc_process is not None:
                rc_process.wait()
                self.__recompile(dae_path)

        if self.__config.make_layer:
            lyr_contents = self.__make_layer()
            lyr_path = os.path.splitext(filepath)[0] + '.lyr'
            utils.generate_file(lyr_path, lyr_contents)

        if not self.__config.save_dae:
            rcdone_path = '{}.rcdone'.format(dae_path)
            utils.remove_file(dae_path)
            utils.remove_file(rcdone_path)

    def __recompile(self, dae_path):
        components = dae_path.split('\\')
        name = components[-1]
        output_path = dae_path[:-len(name)]
        for group in utils.get_export_nodes():
            node_type = utils.get_node_type(group.name)
            allowed = ['cgf', 'cga', 'chr', 'skin']
            if node_type in allowed:
                out_file = '{0}{1}'.format(output_path,
                                           group.name)
                args = [
                    self.__config.rc_path,
                    '/refresh',
                    '/vertexindexformat=u16',
                    out_file]
                if (self.__config.suppress_printouts):
                    args.append('/quiet')
                rc_second_pass = subprocess.Popen(args)

    def __make_layer(self):
        layer_name = "ExportedLayer"
        layer_doc = Document()
        object_layer = layer_doc.createElement("ObjectLayer")
        layer = layer_doc.createElement("Layer")
        layer.setAttribute('name', layer_name)
        layer.setAttribute('GUID', utils.get_guid())
        layer.setAttribute('FullName', layer_name)
        layer.setAttribute('External', '0')
        layer.setAttribute('Exportable', '1')
        layer.setAttribute('ExportLayerPak', '1')
        layer.setAttribute('DefaultLoaded', '0')
        layer.setAttribute('HavePhysics', '1')
        layer.setAttribute('Expanded', '0')
        layer.setAttribute('IsDefaultColor', '1')
        # Layer Objects
        layer_objects = layer_doc.createElement("LayerObjects")
        # Actual Objects
        for group in utils.get_export_nodes():
            if len(group.objects) > 1:
                origin = 0, 0, 0
                rotation = 1, 0, 0, 0
            else:
                origin = group.objects[0].location
                rotation = group.objects[0].delta_rotation_quaternion

            if 'CryExportNode' in group.name:
                object_node = layer_doc.createElement("Object")
                object_node.setAttribute('name', group.name[14:])
                object_node.setAttribute('Type', 'Entity')
                object_node.setAttribute('Id', utils.get_guid())
                object_node.setAttribute(
                    'LayerGUID',
                    layer.getAttribute('GUID'))
                object_node.setAttribute('Layer', layer_name)
                cbPrint(origin)
                positionString = "%s, %s, %s" % origin[:]
                object_node.setAttribute('Pos', positionString)
                rotationString = "%s, %s, %s, %s" % rotation[:]
                object_node.setAttribute('Rotate', rotationString)
                object_node.setAttribute('EntityClass', 'BasicEntity')
                object_node.setAttribute('FloorNumber', '-1')
                object_node.setAttribute('RenderNearest', '0')
                object_node.setAttribute('NoStaticDecals', '0')
                object_node.setAttribute('CreatedThroughPool', '0')
                object_node.setAttribute('MatLayersMask', '0')
                object_node.setAttribute('OutdoorOnly', '0')
                object_node.setAttribute('CastShadow', '1')
                object_node.setAttribute('MotionBlurMultiplier', '1')
                object_node.setAttribute('LodRatio', '100')
                object_node.setAttribute('ViewDistRatio', '100')
                object_node.setAttribute('HiddenInGame', '0')
                properties = layer_doc.createElement("Properties")
                properties.setAttribute('object_Model', '/Objects/%s.cgf'
                                        % group.name[14:])
                properties.setAttribute('bCanTriggerAreas', '0')
                properties.setAttribute('bExcludeCover', '0')
                properties.setAttribute('DmgFactorWhenCollidingAI', '1')
                properties.setAttribute('esFaction', '')
                properties.setAttribute('bHeavyObject', '0')
                properties.setAttribute('bInteractLargeObject', '0')
                properties.setAttribute('bMissionCritical', '0')
                properties.setAttribute('bPickable', '0')
                properties.setAttribute('soclasses_SmartObjectClass', '')
                properties.setAttribute('bUsable', '0')
                properties.setAttribute('UseMessage', '0')
                health = layer_doc.createElement("Health")
                health.setAttribute('bInvulnerable', '1')
                health.setAttribute('MaxHealth', '500')
                health.setAttribute('bOnlyEnemyFire', '1')
                interest = layer_doc.createElement("Interest")
                interest.setAttribute('soaction_Action', '')
                interest.setAttribute('bInteresting', '0')
                interest.setAttribute('InterestLevel', '1')
                interest.setAttribute('Pause', '15')
                interest.setAttribute('Radius', '20')
                interest.setAttribute('bShared', '0')
                vOffset = layer_doc.createElement('vOffset')
                vOffset.setAttribute('x', '0')
                vOffset.setAttribute('y', '0')
                vOffset.setAttribute('z', '0')
                interest.appendChild(vOffset)
                properties.appendChild(health)
                properties.appendChild(interest)
                object_node.appendChild(properties)
                layer_objects.appendChild(object_node)

        layer.appendChild(layer_objects)
        object_layer.appendChild(layer)
        layer_doc.appendChild(object_layer)

        return layer_doc.toprettyxml(indent="  ")


class _TIFConverter:

    def __init__(self, config, source):
        self.__config = config
        self.__images = source
        self.__temp_images = {}
        self.__temp_dir = tempfile.mkdtemp("CryBlend")

    def __call__(self):
        cbPrint(len(self.__images))
        for image in self.__images:
            tiff_path = self.__get_temp_tiff_image_path(image)

            rc_process = run_rc(self.__config.texture_rc_path,
                                tiff_path,
                                self.__get_rc_params())
            rc_process.wait()

        if self.__config.save_tiffs:
            self.__save_tiffs()

        self.__remove_temp_files()

    def __get_rc_params(self):
        params = [
            '/verbose',
            '/threads=cores',
            '/refresh',
            '/targetroot={}'.format(self.__config.textures_dir)]
        if (self.__config.suppress_printouts):
            params.append('/quiet')
        if (self.__config.show_texture_dialog):
            params.append('/userdialog=1')

        return params

    def __get_temp_tiff_image_path(self, image):
        image_path = Path(image.filepath)

        if image_path.get_extension() == ".tif":
            return image_path

        tiff_path = image_path.set_extension("tif")
        tiff_name = tiff_path.get_basename()

        temp_path = Path(self.__temp_dir, tiff_name, ".tif")
        dest_path = Path(self.__config.textures_dir, tiff_name, ".tif")

        if tiff_path != image_path:
            self.__temp_images[temp_path] = dest_path
            self.__save_as_tiff(image, temp_path)

        return temp_path

    def __save_as_tiff(self, image, tiff_path):
        original_path = image.filepath

        try:
            image.filepath_raw = tiff_path
            image.file_format = 'TIFF'
            image.save()

        finally:
            image.filepath = original_path

    def __save_tiffs(self):
        for temp_image, dest_image in self.__temp_images.items():
            cbPrint("Moving tmp image: {!r} to {!r}".format(temp_image,
                                                            dest_image),
                    'debug')
            shutil.move(temp_image, dest_image)

    def __remove_temp_files(self):
        for temp_image in self.__temp_images:
            try:
                os.remove(temp_image)
            except FileNotFoundError:
                pass

        os.removedirs(self.__temp_dir)
        self.__temp_images.clear()


def run_rc(rc_path, files_to_process, params=None):
    cbPrint(rc_path)
    process_params = [rc_path]

    if isinstance(files_to_process, list):
        process_params.extend(files_to_process)
    else:
        process_params.append(files_to_process)

    process_params.extend(params)
    cbPrint(params)
    cbPrint(files_to_process)

    try:
        run_object = subprocess.Popen(process_params)
    except:
        raise exceptions.NoRcSelectedException

    return run_object
