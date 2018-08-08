import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math
from slicer.util import getNode, getNodes
from slicer import modules, app
import time
import Viewpoint

class LumpNavReplay(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LumpNavReplay"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Thomas Vaughan (Queen's University)"]
    self.parent.helpText = """
    This is a small module to allow automated evaluation of tumor tracking in lumpectomy.
    """
    self.parent.acknowledgementText = """
    """

#
# LumpNavReplayWidget
#

class LumpNavReplayWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  
  transducerToProbeFileDialog = None
  sceneFileDialog = None
  recordingFileDialog = None
  trackingFileDialog = None
  
  # treat these two values as enums
  currentDatasetRecordingString  = "Recording"
  currentDatasetTrackingString = "Tracking"
  currentDataset = currentDatasetRecordingString

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    self.logic = LumpNavReplayLogic()

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Controls"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    
    self.transducerToProbeFileLayout = qt.QHBoxLayout()
    self.transducerToProbeFileLabel = qt.QLabel("Transducer to Probe file: ")
    self.transducerToProbeFileLayout.addWidget(self.transducerToProbeFileLabel)
    self.transducerToProbeFileLineEdit = qt.QLineEdit() #qt.QFileDialog()
    self.transducerToProbeFileLineEdit.setToolTip("The directory where the lumpnav data has been saved.")
    self.transducerToProbeFileLayout.addWidget(self.transducerToProbeFileLineEdit)
    self.transducerToProbeFileSelectButton = qt.QPushButton("Select")
    self.transducerToProbeFileLayout.addWidget(self.transducerToProbeFileSelectButton)
    self.transducerToProbeFileSelectButton.connect('clicked()', self.onTransducerToProbeFileSelectButtonPressed)
    parametersFormLayout.addRow(self.transducerToProbeFileLayout)
    
    self.sceneFileLayout = qt.QHBoxLayout()
    self.sceneFileLabel = qt.QLabel("Scene file: ")
    self.sceneFileLayout.addWidget(self.sceneFileLabel)
    self.sceneFileLineEdit = qt.QLineEdit() #qt.QFileDialog()
    self.sceneFileLineEdit.setToolTip("The directory where the lumpnav data has been saved.")
    self.sceneFileLayout.addWidget(self.sceneFileLineEdit)
    self.sceneFileSelectButton = qt.QPushButton("Select")
    self.sceneFileLayout.addWidget(self.sceneFileSelectButton)
    self.sceneFileSelectButton.connect('clicked()', self.onSceneFileSelectButtonPressed)
    parametersFormLayout.addRow(self.sceneFileLayout)
    
    self.recordingFileLayout = qt.QHBoxLayout()
    self.recordingFileLabel = qt.QLabel("Recording file: ")
    self.recordingFileLayout.addWidget(self.recordingFileLabel)
    self.recordingFileLineEdit = qt.QLineEdit() #qt.QFileDialog()
    self.recordingFileLineEdit.setToolTip("The file path to the recording mha file.")
    self.recordingFileLayout.addWidget(self.recordingFileLineEdit)
    self.recordingFileSelectButton = qt.QPushButton("Select")
    self.recordingFileLayout.addWidget(self.recordingFileSelectButton)
    self.recordingFileSelectButton.connect('clicked()', self.onRecordingFileSelectButtonPressed)
    parametersFormLayout.addRow(self.recordingFileLayout)
    
    self.trackingFileLayout = qt.QHBoxLayout()
    self.trackingFileLabel = qt.QLabel("Tracking file: ")
    self.trackingFileLayout.addWidget(self.trackingFileLabel)
    self.trackingFileLineEdit = qt.QLineEdit() #qt.QFileDialog()
    self.trackingFileLineEdit.setToolTip("The file path to the recording mha file.")
    self.trackingFileLayout.addWidget(self.trackingFileLineEdit)
    self.trackingFileSelectButton = qt.QPushButton("Select")
    self.trackingFileLayout.addWidget(self.trackingFileSelectButton)
    self.trackingFileSelectButton.connect('clicked()', self.onTrackingFileSelectButtonPressed)
    parametersFormLayout.addRow(self.trackingFileLayout)
    
    self.loadAllDataButton = qt.QPushButton("Load All Data")
    self.loadAllDataButton.setToolTip("Load the pertinent data for evaluating tumor tracking.")
    parametersFormLayout.addRow(self.loadAllDataButton)
    self.loadAllDataButton.connect('clicked()', self.onLoadAllDataButtonPressed)

    self.switchDataButton = qt.QPushButton("Switch to " + self.currentDatasetTrackingString + " data set")
    self.switchDataButton.setToolTip("Switch between recording and tracking data sets.")
    self.switchDataButton.setEnabled(False)
    parametersFormLayout.addRow(self.switchDataButton)
    self.switchDataButton.connect('clicked()', self.onSwitchDataButtonPressed)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def onTransducerToProbeFileSelectButtonPressed(self):
    if not self.transducerToProbeFileDialog:
      self.transducerToProbeFileDialog = qt.QFileDialog(self.parent)
      self.initializeFileDialog(self.transducerToProbeFileDialog)
    self.transducerToProbeFileDialog.connect("fileSelected(QString)", self.onTransducerToProbeFileSelected)
    self.transducerToProbeFileDialog.show()
    
  def onTransducerToProbeFileSelected(self, filePath):
    self.transducerToProbeFileLineEdit.text = filePath
    
  def onSceneFileSelectButtonPressed(self):
    if not self.sceneFileDialog:
      self.sceneFileDialog = qt.QFileDialog(self.parent)
      self.initializeFileDialog(self.sceneFileDialog)
    self.sceneFileDialog.connect("fileSelected(QString)", self.onSceneFileSelected)
    self.sceneFileDialog.show()
    
  def onSceneFileSelected(self, filePath):
    self.sceneFileLineEdit.text = filePath

  def onRecordingFileSelectButtonPressed(self):
    if not self.recordingFileDialog:
      self.recordingFileDialog = qt.QFileDialog(self.parent)
      self.initializeFileDialog(self.recordingFileDialog)
    self.recordingFileDialog.connect("fileSelected(QString)", self.onRecordingFileSelected)
    self.recordingFileDialog.show()
    
  def onRecordingFileSelected(self, filePath):
    self.recordingFileLineEdit.text = filePath

  def onTrackingFileSelectButtonPressed(self):
    if not self.trackingFileDialog:
      self.trackingFileDialog = qt.QFileDialog(self.parent)
      self.initializeFileDialog(self.trackingFileDialog)
    self.trackingFileDialog.connect("fileSelected(QString)", self.onTrackingFileSelected)
    self.trackingFileDialog.show()
    
  def onTrackingFileSelected(self, filePath):
    self.trackingFileLineEdit.text = filePath
    
  def initializeFileDialog(self, fileDialog):
    fileDialog.options = fileDialog.DontUseNativeDialog
    fileDialog.fileMode = fileDialog.ExistingFile
    fileDialog.acceptMode = fileDialog.AcceptOpen

  def onLoadAllDataButtonPressed(self):
    self.logic.loadAllData(self.transducerToProbeFileLineEdit.text, \
                           self.sceneFileLineEdit.text, \
                           self.recordingFileLineEdit.text, \
                           self.trackingFileLineEdit.text)
    self.currentDataset = self.currentDatasetRecordingString
    self.switchDataButton.setEnabled(True)

  def onSwitchDataButtonPressed(self):
    if (self.currentDataset == self.currentDatasetRecordingString):
      self.logic.changeToTrackingData()
      self.currentDataset = self.currentDatasetTrackingString
      self.switchDataButton.text = "Switch to " + self.currentDatasetRecordingString
    elif (self.currentDataset == self.currentDatasetTrackingString):
      self.logic.changeToRecordingData()
      self.currentDataset = self.currentDatasetRecordingString
      self.switchDataButton.text = "Switch to " + self.currentDatasetTrackingString
    else:
      logging.error("LumpNavReplayWidget is in an unexpected state - current dataset is " + self.currentDataset)
    
  def cleanup(self):
    pass

  def onSelect(self):
    pass

#
# LumpNavReplayLogic
#

class LumpNavReplayLogic(ScriptedLoadableModuleLogic):
    
  def loadAllData(self, transducerToProbeFile, sceneFile, recordingFile, trackingFile): #,trackingFile
    slicer.mrmlScene.Clear(False)
    slicer.util.loadTransform(transducerToProbeFile)
    self.loadScene(sceneFile)
    self.loadRecordingSequences(recordingFile)
    self.loadTrackingSequences(trackingFile)
    self.changeToRecordingData()
    
  def loadScene(self, fileName):
    slicer.util.loadScene(fileName);
    self.referenceToRasNode = slicer.mrmlScene.GetFirstNodeByName("ReferenceToRas")
    self.cauteryTipToCauteryNode = slicer.mrmlScene.GetFirstNodeByName("CauteryTipToCautery")
    self.cauteryModelToCauteryTipNode = slicer.mrmlScene.GetFirstNodeByName("CauteryModelToCauteryTip")
    self.needleTipToNeedleNode = slicer.mrmlScene.GetFirstNodeByName("NeedleTipToNeedle")
    self.needleModelToNeedleTip = slicer.mrmlScene.GetFirstNodeByName("NeedleModelToNeedleTip")
    self.transducerToProbeNode = slicer.mrmlScene.GetFirstNodeByName("TransducerToProbe")
    self.tumorModelNode_Needle = slicer.mrmlScene.GetFirstNodeByName("TumorModel")
    self.cauteryModelNode_CauteryModel = slicer.mrmlScene.GetFirstNodeByName("CauteryModel")
    self.needleModelNode_NeedleModel = slicer.mrmlScene.GetFirstNodeByName("NeedleModel")
    self.setupAutocenter()

  def loadRecordingSequences(self, recordingFile):
    logging.debug("loading \'recording\' sequences")
    recordingFileBaseName = os.path.splitext(os.path.basename(recordingFile))[0]
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':recordingFile})
    self.recordingData_browserNode = slicer.mrmlScene.GetFirstNodeByName(recordingFileBaseName)
    self.recordingData_trackerToReferenceNode = self.initializeLinearTransformNode(recordingFileBaseName + "-TrackerToReference")
    self.recordingData_needleToTrackerNode = self.initializeLinearTransformNode(recordingFileBaseName + "-NeedleToTracker")
    self.recordingData_cauteryToTrackerNode = self.initializeLinearTransformNode(recordingFileBaseName + "-CauteryToTracker")
    self.probeToTrackerNode = self.initializeLinearTransformNode(recordingFileBaseName + "-ProbeToTracker")
    self.imageToTransducerNode = self.initializeLinearTransformNode(recordingFileBaseName + "-ImageToTransducer")
    self.imageNode = getNode(recordingFileBaseName + "-Image")
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode
    self.setupResliceDriver()
    self.assignSlicerVariables()

  def loadTrackingSequences(self, trackingFile):
    logging.debug("loading \'tracking\' sequences")
    trackingFileBaseName = os.path.splitext(os.path.basename(trackingFile))[0]
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':trackingFile})
    self.trackingData_browserNode = slicer.mrmlScene.GetFirstNodeByName(trackingFileBaseName)
    self.trackingData_trackerToReferenceNode = self.initializeLinearTransformNode(trackingFileBaseName + "-TrackerToReference")
    self.trackingData_needleToTrackerNode = self.initializeLinearTransformNode(trackingFileBaseName + "-NeedleToTracker")
    self.trackingData_cauteryToTrackerNode = self.initializeLinearTransformNode(trackingFileBaseName + "-CauteryToTracker")
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode
    self.assignSlicerVariables()

  def changeToRecordingData(self):
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode
    self.updateModelVisibility(inTrackingMode=False)
    self.setupTransformHierarchy()
    slicer.modules.sequencebrowser.setToolBarActiveBrowserNode(self.recordingData_browserNode)

  def changeToTrackingData(self):
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode
    self.updateModelVisibility(inTrackingMode=True)
    self.setupTransformHierarchy()
    slicer.modules.sequencebrowser.setToolBarActiveBrowserNode(self.trackingData_browserNode)

  def updateModelVisibility(self, inTrackingMode=True):
    inRecordingMode = not inTrackingMode
    if self.imageNode:
      self.imageNode.GetDisplayNode().SetVisibility(inRecordingMode)

  def setupTransformHierarchy(self):
    logging.debug("setting up transform hierarchy")

    self.trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.cauteryToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.cauteryTipToCauteryNode.SetAndObserveTransformNodeID(self.cauteryToTrackerNode.GetID())
    self.cauteryModelToCauteryTipNode.SetAndObserveTransformNodeID(self.cauteryTipToCauteryNode.GetID())
    self.cauteryModelNode_CauteryModel.SetAndObserveTransformNodeID(self.cauteryModelToCauteryTipNode.GetID())
    
    self.needleToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.needleTipToNeedleNode.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())
    self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedleNode.GetID())
    self.needleModelNode_NeedleModel.SetAndObserveTransformNodeID(self.needleModelToNeedleTip.GetID())
    self.tumorModelNode_Needle.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())

    self.probeToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.transducerToProbeNode.SetAndObserveTransformNodeID(self.probeToTrackerNode.GetID())
    self.imageToTransducerNode.SetAndObserveTransformNodeID(self.transducerToProbeNode.GetID())
    if self.imageNode:
      self.imageNode.SetAndObserveTransformNodeID(self.imageToTransducerNode.GetID())
  
  def assignSlicerVariables(self):
    class empty:
      pass
    slicer.lumpnavreplay = empty()
    slicer.lumpnavreplay.referenceToRasNode = self.referenceToRasNode
    slicer.lumpnavreplay.trackerToReferenceNode = self.trackerToReferenceNode
    slicer.lumpnavreplay.cauteryToTrackerNode = self.cauteryToTrackerNode
    slicer.lumpnavreplay.cauteryTipToCauteryNode = self.cauteryTipToCauteryNode
    slicer.lumpnavreplay.cauteryModelToCauteryTipNode = self.cauteryModelToCauteryTipNode
    slicer.lumpnavreplay.cauteryModelNode_CauteryModel = self.cauteryModelNode_CauteryModel
    slicer.lumpnavreplay.needleToTrackerNode = self.needleToTrackerNode
    slicer.lumpnavreplay.needleTipToNeedleNode = self.needleTipToNeedleNode
    slicer.lumpnavreplay.needleModelToNeedleTip = self.needleModelToNeedleTip
    slicer.lumpnavreplay.needleModelNode_NeedleModel = self.needleModelNode_NeedleModel
    slicer.lumpnavreplay.tumorModelNode_Needle = self.tumorModelNode_Needle
    slicer.lumpnavreplay.probeToTrackerNode = self.probeToTrackerNode
    slicer.lumpnavreplay.transducerToProbeNode = self.transducerToProbeNode
    slicer.lumpnavreplay.imageToTransducerNode = self.imageToTransducerNode
    if self.imageNode:
      slicer.lumpnavreplay.imageNode = self.imageNode
  
  # Setting autocenter parameters to match LumpNav
  def setupAutocenter(self):
    viewpointLogic = Viewpoint.ViewpointLogic()

    leftView = slicer.mrmlScene.GetNodeByID('vtkMRMLViewNode1')
    rightView = slicer.mrmlScene.GetNodeByID('vtkMRMLViewNode2')
    bottomView = slicer.mrmlScene.GetNodeByID('vtkMRMLViewNode3')
    heightViewCoordLimits = 0.6;
    widthViewCoordLimits = 0.9;

    leftViewNodeViewpoint = viewpointLogic.getViewpointForViewNode(leftView)
    leftViewNodeViewpoint.setViewNode(leftView)
    leftViewNodeViewpoint.autoCenterSetSafeXMinimum(-widthViewCoordLimits)
    leftViewNodeViewpoint.autoCenterSetSafeXMaximum(widthViewCoordLimits)
    leftViewNodeViewpoint.autoCenterSetSafeYMinimum(-heightViewCoordLimits)
    leftViewNodeViewpoint.autoCenterSetSafeYMaximum(heightViewCoordLimits)
    leftViewNodeViewpoint.autoCenterSetModelNode(self.tumorModelNode_Needle)
    leftViewNodeViewpoint.autoCenterStart()

    rightViewNodeViewpoint = viewpointLogic.getViewpointForViewNode(rightView)
    rightViewNodeViewpoint.setViewNode(rightView)
    rightViewNodeViewpoint.autoCenterSetSafeXMinimum(-widthViewCoordLimits)
    rightViewNodeViewpoint.autoCenterSetSafeXMaximum(widthViewCoordLimits)
    rightViewNodeViewpoint.autoCenterSetSafeYMinimum(-heightViewCoordLimits)
    rightViewNodeViewpoint.autoCenterSetSafeYMaximum(heightViewCoordLimits)
    rightViewNodeViewpoint.autoCenterSetModelNode(self.tumorModelNode_Needle)
    rightViewNodeViewpoint.autoCenterStart()

    # Earlier surgeries did not use Triple 3D view
    if bottomView :
      bottomViewNodeViewpoint = viewpointLogic.getViewpointForViewNode(bottomView)
      bottomViewNodeViewpoint.setViewNode(bottomView)
      bottomViewNodeViewpoint.autoCenterSetSafeXMinimum(-widthViewCoordLimits)
      bottomViewNodeViewpoint.autoCenterSetSafeXMaximum(widthViewCoordLimits)
      bottomViewNodeViewpoint.autoCenterSetSafeYMinimum(-heightViewCoordLimits)
      bottomViewNodeViewpoint.autoCenterSetSafeYMaximum(heightViewCoordLimits)
      bottomViewNodeViewpoint.autoCenterSetModelNode(self.tumorModelNode_Needle)
      bottomViewNodeViewpoint.autoCenterStart()
      
  def setupResliceDriver(self):
    sliceNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSliceNode")
    imageNode = self.imageNode
    slicer.modules.volumereslicedriver.logic().SetDriverForSlice(imageNode.GetID(),sliceNode)

  def initializeLinearTransformNode(self,name):
    logging.debug('initializeLinearTransformNode')
    transformNode = slicer.mrmlScene.GetFirstNodeByName(name)
    if not transformNode:
      transformNode=slicer.vtkMRMLLinearTransformNode()
      transformNode.SetName(name)
      slicer.mrmlScene.AddNode(transformNode)
    return transformNode

class LumpNavReplayTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_LumpNavReplay1()

  def test_LumpNavReplay1(self):
    self.delayDisplay('No tests implemented yet!')
