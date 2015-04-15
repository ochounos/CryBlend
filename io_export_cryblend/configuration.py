#------------------------------------------------------------------------------
# Name:        configuration.py
# Purpose:     Storing CryBlend configuration settings
#
# Author:      Mikołaj Milej
#
# Created:     02/10/2013
# Copyright:   (c) Mikołaj Milej 2013
# Licence:     GPLv2+
#------------------------------------------------------------------------------

# <pep8-80 compliant>


from io_export_cryblend.outPipe import cbPrint
from io_export_cryblend.utils import Path
import bpy
import os
import pickle


class __Configuration:
    __CONFIG_PATH = bpy.utils.user_resource('CONFIG',
                                            path='scripts',
                                            create=True)
    __CONFIG_FILENAME = 'cryblend.cfg'
    __CONFIG_FILEPATH = os.path.join(__CONFIG_PATH, __CONFIG_FILENAME)
    __DEFAULT_CONFIGURATION = {'RC_PATH': r'',
                               'TEXTURE_RC_PATH': r'',
                               'TEXTURES_DIR': r''}

    def __init__(self):
        self.__CONFIG = self.__load({})

    @property
    def rc_path(self):
        return self.__CONFIG['RC_PATH']

    @rc_path.setter
    def rc_path(self, value):
        self.__CONFIG['RC_PATH'] = value

    @property
    def texture_rc_path(self):
        if (not self.__CONFIG['TEXTURE_RC_PATH']):
            return self.rc_path

        return self.__CONFIG['TEXTURE_RC_PATH']

    @texture_rc_path.setter
    def texture_rc_path(self, value):
        self.__CONFIG['TEXTURE_RC_PATH'] = value

    @property
    def textures_dir(self):
        return self.__CONFIG['TEXTURES_DIR']

    @textures_dir.setter
    def textures_dir(self, value):
        self.__CONFIG['TEXTURES_DIR'] = value

    def configured(self):
        if (self.rc_configured() and
                self.texture_rc_configured() and
                self.textures_dir_configured()):
            return True

        return False

    def rc_configured(self):
        path = Path(self.__CONFIG['RC_PATH'])
        cbPrint(path.get_extension())
        if len(path) > 0 and path.get_basename() == "rc":
            return True

        return False

    def texture_rc_configured(self):
        path = Path(self.__CONFIG['TEXTURE_RC_PATH'])
        if len(path) > 0 and path.get_basename() == "rc":
            return True

        return False

    def textures_dir_configured(self):
        path = Path(self.__CONFIG['TEXTURES_DIR'])
        if len(path) > 0:
            return True

        return False

    def save(self):
        cbPrint('Saving configuration file.', 'debug')

        if os.path.isdir(self.__CONFIG_PATH):
            try:
                with open(self.__CONFIG_FILEPATH, 'wb') as f:
                    pickle.dump(self.__CONFIG, f, -1)
                    cbPrint('Configuration file saved.')

                cbPrint('Saved %s' % self.__CONFIG_FILEPATH)

            except:
                cbPrint('[IO] can not write: %s' % self.__CONFIG_FILEPATH,
                        'error')

        else:
            cbPrint('Configuration file path is missing %s'
                    % self.__CONFIG_PATH,
                    'error')

    def __load(self, current_configuration):
        new_configuration = {}
        new_configuration.update(self.__DEFAULT_CONFIGURATION)
        new_configuration.update(current_configuration)

        if os.path.isfile(self.__CONFIG_FILEPATH):
            try:
                with open(self.__CONFIG_FILEPATH, 'rb') as f:
                    new_configuration.update(pickle.load(f))
                    cbPrint('Configuration file loaded.')
            except:
                cbPrint('[IO] can not read: %s' % self.__CONFIG_FILEPATH,
                        'error')

        return new_configuration


Configuration = __Configuration()
