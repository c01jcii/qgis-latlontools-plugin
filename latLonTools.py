from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.core import QgsCoordinateTransform, QgsVectorLayer, QgsRectangle, QgsPoint, QgsPointXY, QgsGeometry, QgsWkbTypes, QgsProject, QgsApplication
from qgis.gui import QgsRubberBand
import processing

from .zoomToLatLon import ZoomToLatLon
from .multizoom import MultiZoomWidget
from .copyLatLonTool import CopyLatLonTool
from .showOnMapTool import ShowOnMapTool
from .settings import SettingsWidget
from .provider import LatLonToolsProvider
import os
import webbrowser


class LatLonTools:
    digitizerDialog = None
    toMGRSDialog = None
    MGRStoLayerDialog = None
    geom2FieldDialog = None
    
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.crossRb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.crossRb.setColor(Qt.red)
        self.provider = LatLonToolsProvider()        
        self.toolbar = self.iface.addToolBar('Lat Lon Tools Toolbar')
        self.toolbar.setObjectName('LatLonToolsToolbar')

    def initGui(self):
        '''Initialize Lot Lon Tools GUI.'''
        # Initialize the Settings Dialog box
        self.settingsDialog = SettingsWidget(self, self.iface, self.iface.mainWindow())
        self.mapTool = CopyLatLonTool(self.settingsDialog, self.iface)
        self.showMapTool = ShowOnMapTool(self.settingsDialog, self.iface)
        
        # Add Interface for Coordinate Capturing
        icon = QIcon(os.path.dirname(__file__) + "/images/copyicon.png")
        self.copyAction = QAction(icon, "Copy Latitude, Longitude", self.iface.mainWindow())
        self.copyAction.setObjectName('latLonToolsCopy')
        self.copyAction.triggered.connect(self.startCapture)
        self.copyAction.setCheckable(True)
        self.toolbar.addAction(self.copyAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyAction)
        
        # Add Interface for External Map
        icon = QIcon(os.path.dirname(__file__) + "/images/mapicon.png")
        self.externMapAction = QAction(icon, "Show in External Map", self.iface.mainWindow())
        self.externMapAction.setObjectName('latLonToolsExternalMap')
        self.externMapAction.triggered.connect(self.setShowMapTool)
        self.externMapAction.setCheckable(True)
        self.toolbar.addAction(self.externMapAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.externMapAction)

        # Add Interface for Zoom to Coordinate
        icon = QIcon(os.path.dirname(__file__) + "/images/zoomicon.png")
        self.zoomToAction = QAction(icon, "Zoom To Latitude, Longitude", self.iface.mainWindow())
        self.zoomToAction.setObjectName('latLonToolsZoom')
        self.zoomToAction.triggered.connect(self.showZoomToDialog)
        self.toolbar.addAction(self.zoomToAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.zoomToAction)

        self.zoomToDialog = ZoomToLatLon(self, self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()
        
        # Add Interface for Multi point zoom
        icon = QIcon(os.path.dirname(__file__) + '/images/multizoom.png')
        self.multiZoomToAction = QAction(icon, "Multi-location Zoom", self.iface.mainWindow())
        self.multiZoomToAction.setObjectName('latLonToolsMultiZoom')
        self.multiZoomToAction.triggered.connect(self.multiZoomTo)
        self.toolbar.addAction(self.multiZoomToAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.multiZoomToAction)

        self.multiZoomDialog = MultiZoomWidget(self, self.settingsDialog, self.iface.mainWindow())
        self.multiZoomDialog.hide()
        self.multiZoomDialog.setFloating(True)
        
        # Add To MGRS conversion
        menu = QMenu()
        icon = QIcon(os.path.dirname(__file__) + '/images/geom2field.png')
        action = menu.addAction(icon, "Geometry to Field", self.geom2Field)
        action.setObjectName('latLonToolsGeom2Field')
        icon = QIcon(os.path.dirname(__file__) + '/images/pluscodes.png')
        action = menu.addAction(icon, "Plus Codes to point layer", self.PlusCodestoLayer)
        action.setObjectName('latLonToolsPlusCodes2Geom')
        action = menu.addAction(icon, "Point layer to Plus Codes", self.toPlusCodes)
        action.setObjectName('latLonToolsGeom2PlusCodes')
        icon = QIcon(os.path.dirname(__file__) + '/images/mgrs2point.png')
        action = menu.addAction(icon, "MGRS to point layer", self.MGRStoLayer)
        action.setObjectName('latLonToolsMGRS2Geom')
        icon = QIcon(os.path.dirname(__file__) + '/images/point2mgrs.png')
        action = menu.addAction(icon, "Point layer to MGRS", self.toMGRS)
        action.setObjectName('latLonToolsGeom2MGRS')
        self.toMGRSAction = QAction(icon, "Conversions", self.iface.mainWindow())
        self.toMGRSAction.setMenu(menu)
        self.iface.addPluginToMenu('Lat Lon Tools', self.toMGRSAction)
        
        # Add to Digitize Toolbar
        icon = QIcon(os.path.dirname(__file__) + '/images/latLonDigitize.png')
        self.digitizeAction = QAction(icon, "Lat Lon Digitize", self.iface.mainWindow())
        self.digitizeAction.setObjectName('latLonToolsDigitize')
        self.digitizeAction.triggered.connect(self.digitizeClicked)
        self.digitizeAction.setEnabled(False)
        self.toolbar.addAction(self.digitizeAction)
        self.iface.addPluginToMenu('Lat Lon Tools', self.digitizeAction)
        
        # Initialize the Settings Dialog Box
        settingsicon = QIcon(os.path.dirname(__file__) + '/images/settings.png')
        self.settingsAction = QAction(settingsicon, "Settings", self.iface.mainWindow())
        self.settingsAction.setObjectName('latLonToolsSettings')
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Lat Lon Tools', self.settingsAction)
        
        # Help
        icon = QIcon(os.path.dirname(__file__) + '/images/help.png')
        self.helpAction = QAction(icon, "Help", self.iface.mainWindow())
        self.helpAction.setObjectName('latLonToolsHelp')
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Lat Lon Tools', self.helpAction)
        
        
        self.iface.currentLayerChanged.connect(self.currentLayerChanged)
        self.canvas.mapToolSet.connect(self.unsetTool)
        self.enableDigitizeTool()
        # Add the processing provider
        
        QgsApplication.processingRegistry().addProvider(self.provider)
                
    def unsetTool(self, tool):
        '''Uncheck the Copy Lat Lon tool'''
        try:
            if not isinstance(tool, CopyLatLonTool):
                self.copyAction.setChecked(False)
                self.multiZoomDialog.stopCapture()
                self.mapTool.capture4326 = False
            if not isinstance(tool, ShowOnMapTool):
                self.externMapAction.setChecked(False)
        except:
            pass

    def unload(self):
        '''Unload LatLonTools from the QGIS interface'''
        self.zoomToDialog.removeMarker()
        self.multiZoomDialog.removeMarkers()
        self.canvas.unsetMapTool(self.mapTool)
        self.canvas.unsetMapTool(self.showMapTool)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.externMapAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.zoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.multiZoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.toMGRSAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.settingsAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.helpAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.digitizeAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        self.iface.removeDockWidget(self.multiZoomDialog)
        # Remove Toolbar Icons
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removeToolBarIcon(self.zoomToAction)
        self.iface.removeToolBarIcon(self.externMapAction)
        self.iface.removeToolBarIcon(self.multiZoomToAction)
        self.iface.removeToolBarIcon(self.digitizeAction)
        del self.toolbar
        
        self.geom2FieldDialog = None
        self.MGRStoLayerDialog = None
        self.toMGRSDialog = None
        self.zoomToDialog = None
        self.multiZoomDialog = None
        self.settingsDialog = None
        self.showMapTool = None
        self.mapTool = None
        self.digitizerDialog = None
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def startCapture(self):
        '''Set the focus of the copy coordinate tool and check it'''
        self.copyAction.setChecked(True)
        self.canvas.setMapTool(self.mapTool)

    def setShowMapTool(self):
        '''Set the focus of the external map tool and check it'''
        self.externMapAction.setChecked(True)
        self.canvas.setMapTool(self.showMapTool)

    def showZoomToDialog(self):
        '''Show the zoom to docked widget.'''
        self.zoomToDialog.show()

    def multiZoomTo(self):
        '''Display the Multi-zoom to dialog box'''
        self.multiZoomDialog.show()

    def geom2Field(self):
        '''Convert layer geometry to a text string'''
        if self.geom2FieldDialog == None:
            from .geom2field import Geom2FieldWidget
            self.geom2FieldDialog = Geom2FieldWidget(self.iface, self.iface.mainWindow())
        self.geom2FieldDialog.show()

    def toMGRS(self):
        '''Display the to MGRS  dialog box'''
        results = processing.execAlgorithmDialog('latlontools:point2mgrs', {})

    def MGRStoLayer(self):
        '''Display the to MGRS  dialog box'''
        results = processing.execAlgorithmDialog('latlontools:mgrs2point', {})

    def toPlusCodes(self):
        results = processing.execAlgorithmDialog('latlontools:point2pluscodes', {})

    def PlusCodestoLayer(self):
        results = processing.execAlgorithmDialog('latlontools:pluscodes2point', {})
    
    def settings(self):
        '''Show the settings dialog box'''
        self.settingsDialog.show()
        
    def help(self):
        '''Display a help page'''
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)
        
    def settingsChanged(self):
        # Settings may have changed so we need to make sure the zoomToDialog window is configured properly
        self.zoomToDialog.configure()
        self.multiZoomDialog.settingsChanged()
            
 
    def zoomTo(self, srcCrs, lat, lon):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(srcCrs, canvasCrs, QgsProject.instance())
        x, y = transform.transform(float(lon), float(lat))
            
        rect = QgsRectangle(x,y,x,y)
        self.canvas.setExtent(rect)

        pt = QgsPointXY(x,y)
        self.highlight(pt)
        self.canvas.refresh()
        return pt
        
    def highlight(self, point):
        currExt = self.canvas.extent()
        
        leftPt = QgsPoint(currExt.xMinimum(),point.y())
        rightPt = QgsPoint(currExt.xMaximum(),point.y())
        
        topPt = QgsPoint(point.x(),currExt.yMaximum())
        bottomPt = QgsPoint(point.x(),currExt.yMinimum())
        
        horizLine = QgsGeometry.fromPolyline( [ leftPt , rightPt ] )
        vertLine = QgsGeometry.fromPolyline( [ topPt , bottomPt ] )
        
        self.crossRb.reset(QgsWkbTypes.LineGeometry)
        self.crossRb.addGeometry(horizLine, None)
        self.crossRb.addGeometry(vertLine, None)
        
        QTimer.singleShot(700, self.resetRubberbands)
        
    def resetRubberbands(self):
        self.crossRb.reset()
        
    def digitizeClicked(self):
        if self.digitizerDialog == None:
            from .digitizer import DigitizerWidget
            self.digitizerDialog = DigitizerWidget(self, self.iface, self.iface.mainWindow())
        self.digitizerDialog.show()
        
    def currentLayerChanged(self):
        layer = self.iface.activeLayer()
        if layer != None:
            try:
                layer.editingStarted.disconnect(self.layerEditingChanged)
            except:
                pass
            try:
                layer.editingStopped.disconnect(self.layerEditingChanged)
            except:
                pass
            
            if isinstance(layer, QgsVectorLayer):
                layer.editingStarted.connect(self.layerEditingChanged)
                layer.editingStopped.connect(self.layerEditingChanged)
                
        self.enableDigitizeTool()

    def layerEditingChanged(self):
        self.enableDigitizeTool()

    def enableDigitizeTool(self):
        self.digitizeAction.setEnabled(False)
        layer = self.iface.activeLayer()
        
        if layer != None and isinstance(layer, QgsVectorLayer) and (layer.geometryType() == QgsWkbTypes.PointGeometry) and layer.isEditable():
            self.digitizeAction.setEnabled(True)
        else:
            if self.digitizerDialog != None:
                self.digitizerDialog.close()
