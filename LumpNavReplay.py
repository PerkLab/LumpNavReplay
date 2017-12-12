import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math
from slicer.util import getNode, getNodes
from slicer import modules, app
import time

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

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    self.logic = LumpNavReplayLogic()

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    
    self.evaluateTumorTrackingLabel = qt.QLabel("Evaluate Tumor Tracking")
    parametersFormLayout.addRow(self.evaluateTumorTrackingLabel)
    self.layout.addStretch(1)
    
    self.dataDirectoryDialog = qt.QLineEdit() #qt.QFileDialog()
    self.dataDirectoryDialog.setToolTip("The directory where the lumpnav data has been saved.")
    parametersFormLayout.addRow(self.dataDirectoryDialog)
    
    self.recordingFileDialog = qt.QLineEdit() #qt.QFileDialog()
    self.recordingFileDialog.setToolTip("The file path to the recording mha file.")
    parametersFormLayout.addRow(self.recordingFileDialog)
    
    #self.trackingFileDialog = qt.QLineEdit() #qt.QFileDialog()
    #self.trackingFileDialog.setToolTip("The file path to the tracking mha file.")
    #parametersFormLayout.addRow(self.trackingFileDialog)
    
    self.loadAllDataButton = qt.QPushButton("Load All Data")
    self.loadAllDataButton.setToolTip("Load the pertinent data for evaluating tumor tracking.")
    parametersFormLayout.addRow(self.loadAllDataButton)
    self.loadAllDataButton.connect('clicked()', self.onLoadAllDataButtonPressed)

    #self.changeToRecordingDataButton = qt.QPushButton("Change to Recording")
    #self.changeToRecordingDataButton.setToolTip("Switch to Recording Data (preprocessing).")
    #parametersFormLayout.addRow(self.changeToRecordingDataButton)
    #self.changeToRecordingDataButton.connect('clicked()', self.onChangeToRecordingDataButtonPressed)

    #self.changeToTrackingDataButton = qt.QPushButton("Change to Tracking")
    #self.changeToTrackingDataButton.setToolTip("Switch to Tracking Data (evaluation).")
    #parametersFormLayout.addRow(self.changeToTrackingDataButton)
    #self.changeToTrackingDataButton.connect('clicked()', self.onChangeToTrackingDataButtonPressed)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()
  
  def onLoadAllDataButtonPressed(self):
    self.logic.loadAllData(self.dataDirectoryDialog.text,self.recordingFileDialog.text) #,self.trackingFileDialog.text

  def onChangeToRecordingDataButtonPressed(self):
    self.logic.changeToRecordingData()

  def onChangeToTrackingDataButtonPressed(self):
    self.logic.changeToTrackingData()
    
  def cleanup(self):
    pass

  def onSelect(self):
    pass

#
# LumpNavReplayLogic
#

class LumpNavReplayLogic(ScriptedLoadableModuleLogic):
    
  def loadAllData(self, lumpNavDirectory, recordingFile): #,trackingFile
    self.lumpNavDirectory = lumpNavDirectory
    self.recordingFile = recordingFile
    #self.trackingFile = trackingFile
    self.loadAllTransforms()
    self.loadRecordingSequences()
    #self.loadTrackingSequences()
    self.loadAllModels()
    self.changeToRecordingData()

  def loadAllTransforms(self):
    logging.debug("loading transforms")

    # These are necessary for constructing visualizations
    self.referenceToRasNode = self.loadLinearTransformNode(self.lumpNavDirectory, "ReferenceToRas")
    self.cauteryTipToCauteryNode = self.loadLinearTransformNode(self.lumpNavDirectory, "CauteryTipToCautery")
    self.cauteryModelToCauteryTipNode = self.loadLinearTransformNode(self.lumpNavDirectory, "CauteryModelToCauteryTip")

    self.needleTipToNeedleNode = self.loadLinearTransformNode(self.lumpNavDirectory, "NeedleTipToNeedle")
    self.needleModelToNeedleTip = self.loadLinearTransformNode(self.lumpNavDirectory, "NeedleModelToNeedleTip")
    
    # For ultrasound images
    self.transducerToProbeNode = self.loadLinearTransformNode(self.lumpNavDirectory, "TransducerToProbe")

  def loadAllModels(self):
    logging.debug("loading models")

    self.removeExistingNodes("TumorModel*")

    # Tumor models need to be reloaded, even if they already exist in the scene
    slicer.util.loadModel(self.lumpNavDirectory + "TumorModel.vtk")
    self.tumorModelNode_Needle = slicer.util.getNode("TumorModel*")
    if (not self.tumorModelNode_Needle):
      logging.warning("No tumor model found. Using sphere as placeholder.")
      self.tumorModelNode_Needle = slicer.modules.createmodels.logic().CreateSphere(10.0)
      self.tumorModelNode_Needle=slicer.util.getNode(pattern="SphereModel")
    self.tumorModelNode_Needle.SetName("TumorModel_Needle")
    self.tumorModelNode_Needle.GetDisplayNode().SetColor(0.0, 1.0, 0.0)
    self.tumorModelNode_Needle.GetDisplayNode().SetOpacity(0.5)
    self.tumorModelNode_Needle.GetDisplayNode().SliceIntersectionVisibilityOn()

    # These models are constant, so it's okay to re-use these if they exist already
    self.cauteryModelNode_CauteryModel=slicer.util.getNode(pattern="CauteryModel_Cautery")
    if (not self.cauteryModelNode_CauteryModel):
      slicer.modules.createmodels.logic().CreateNeedle(60, 1.0, 0, 0)
      self.cauteryModelNode_CauteryModel=slicer.util.getNode(pattern="NeedleModel")
    self.cauteryModelNode_CauteryModel.SetName("CauteryModel_Cautery")
    self.cauteryModelNode_CauteryModel.GetDisplayNode().SetColor(1.0, 1.0, 0.0)
    self.cauteryModelNode_CauteryModel.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.needleModelNode_NeedleModel=slicer.util.getNode(pattern="NeedleModel_NeedleModelOriginal")
    if (not self.needleModelNode_NeedleModel):
      slicer.modules.createmodels.logic().CreateNeedle(60, 1.0, 0, 0)
      self.needleModelNode_NeedleModel=slicer.util.getNode(pattern="NeedleModel")
    self.needleModelNode_NeedleModel.SetName("NeedleModel_NeedleModelOriginal")
    self.needleModelNode_NeedleModel.GetDisplayNode().SetColor(0.0, 0.5, 0.5)
    self.needleModelNode_NeedleModel.GetDisplayNode().SetOpacity(0.25)
    self.needleModelNode_NeedleModel.GetDisplayNode().SliceIntersectionVisibilityOn()

  def loadRecordingSequences(self):
    logging.debug("loading \'recording\' sequences")
    self.removeExistingNodes("recordingData*")
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':self.recordingFile})
    #slicer.vtkSlicerMetafileImporterLogic().ReadSequenceMetafile(self.lumpNavDirectory + "recordingData.mha")
    self.recordingData_trackerToReferenceNode = self.initializeLinearTransformNode("recordingData*-TrackerToReference")
    self.recordingData_needleToTrackerNode = self.initializeLinearTransformNode("recordingData*-NeedleToTracker")
    self.recordingData_cauteryToTrackerNode = self.initializeLinearTransformNode("recordingData*-CauteryToTracker")
    self.probeToTrackerNode = self.initializeLinearTransformNode("recordingData*-ProbeToTracker")
    self.imageToTransducerNode = self.initializeLinearTransformNode("recordingData*-ImageToTransducer")
    self.imageNode = getNode("recordingData*-Image")
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode

  def loadTrackingSequences(self):
    logging.debug("loading \'tracking\' sequences")
    self.removeExistingNodes("trackingData*")
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':self.trackingFile})
    #slicer.vtkSlicerMetafileImporterLogic().ReadSequenceMetafile(self.lumpNavDirectory + "trackingData.mha")
    self.trackingData_trackerToReferenceNode = self.initializeLinearTransformNode("trackingData*-TrackerToReference")
    self.trackingData_needleToTrackerNode = self.initializeLinearTransformNode("trackingData*-NeedleToTracker")
    self.trackingData_cauteryToTrackerNode = self.initializeLinearTransformNode("trackingData*-CauteryToTracker")
    self.probeToTrackerNode = self.initializeLinearTransformNode("recordingData*-ProbeToTracker")
    self.imageToTransducerNode = self.initializeLinearTransformNode("recordingData*-ImageToTransducer")
    self.imageNode = getNode("recordingData*-Image")
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode

  def changeToRecordingData(self):
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode
    self.updateModelVisibility(inTrackingMode=False)
    self.setupTransformHierarchy()

  def changeToTrackingData(self):
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode
    self.updateModelVisibility(inTrackingMode=True)
    self.setupTransformHierarchy()

  def updateModelVisibility(self, inTrackingMode=True):
    inRecordingMode = not inTrackingMode
    if self.imageNode:
      self.imageNode.GetDisplayNode().SetVisibility(inRecordingMode)

  def setupTransformHierarchy(self):
    logging.debug("setting up transform hierarchy")

    # reset all sequence nodes to the top of the transform hierarchy,
    # only those in the changeToXXXData will be used
    self.recordingData_trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.recordingData_needleToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.recordingData_cauteryToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    #self.trackingData_trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    #self.trackingData_needleToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    #self.trackingData_cauteryToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())

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

  def copyPolyDataFromSourceToTargetModelNode(self, sourceNode, targetNode):
    if not sourceNode:
      logging.error("No source node. Aborting.")
      return
    if not targetNode:
      logging.error("No target node. Aborting.")
      return
    copiedModelPolyData = vtk.vtkPolyData()
    copiedModelPolyData.DeepCopy(sourceNode.GetPolyData())
    targetNode.SetAndObservePolyData(copiedModelPolyData)
    
  def loadLinearTransformNode(self, directory, name):
    node = slicer.util.getNode(name + "*")
    if node:
      slicer.mrmlScene.RemoveNode(node) # reload, don't re-use
    slicer.util.loadTransform(directory + name + ".h5")
    #slicer.app.coreIOManager().loadNodes('LinearTransform',{'fileName':directory+name+".h5"})
    node = slicer.util.getNode(name + "*")
    if not node:
      node = self.initializeLinearTransformNode(name)
    return node

  def loadMarkupsNode(self, directory, name):
    node = slicer.util.getNode(name + '*')
    if node:
      slicer.mrmlScene.RemoveNode(node) # reload, don't re-use
    slicer.util.loadMarkupsFiducialList(directory + name + ".fcsv")
    #slicer.app.coreIOManager().loadNodes('MarkupsFiducials',{'fileName':self.lumpNavDirectory+name+".fcsv"})
    node = slicer.util.getNode(name + "*")
    if not node:
      node = self.initializeMarkupsNode(name)
    return node
  
  def initializeLinearTransformNode(self,name):
    logging.debug('initializeLinearTransformNode')
    transformNode = slicer.util.getNode(name)
    if not transformNode:
      transformNode=slicer.vtkMRMLLinearTransformNode()
      transformNode.SetName(name)
      slicer.mrmlScene.AddNode(transformNode)
    return transformNode

  def initializeMarkupsNode(self,name):
    logging.debug('initializeMarkupsNode')
    markupsNode = slicer.util.getNode(name)
    if not markupsNode:
      markupsNode=slicer.vtkMRMLMarkupsFiducialNode()
      markupsNode.SetName(name)
      slicer.mrmlScene.AddNode(markupsNode)
    return markupsNode
    
  def removeExistingNodes(self,baseName):
    node = slicer.util.getNode(baseName)
    while node:
      slicer.mrmlScene.RemoveNode(node)
      node = slicer.util.getNode(baseName)

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
