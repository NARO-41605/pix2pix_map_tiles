# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QPix2pix
                                 A QGIS plugin
 test
                             -------------------
        begin                : 2017-09-29
        copyright            : (C) 2017 by nss
        email                : kobayashi@nssv.co.jp
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QPix2pix class from file QPix2pix.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .qpix2pix import QPix2pix
    return QPix2pix(iface)
