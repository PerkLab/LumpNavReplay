import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math
from slicer.util import getNode, getNodes
from slicer import modules, app
import time

class TumorTrackingEval(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "TumorTrackingEval"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Thomas Vaughan (Queen's University)"]
    self.parent.helpText = """
    This is a small module to allow automated evaluation of tumor tracking in lumpectomy.
    """
    self.parent.acknowledgementText = """
    """

#
# TumorTrackingEvalWidget
#

class TumorTrackingEvalWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    self.logic = TumorTrackingEvalLogic()

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
    
    self.evaluateTumorTrackingLabel = qt.QLabel("Evaluate Tumor Tracking")
    parametersFormLayout.addRow(self.evaluateTumorTrackingLabel)
    self.layout.addStretch(1)
    
    self.directoryDialog = qt.QLineEdit() #qt.QFileDialog()
    #self.directoryDialog.setFileMode(self.directoryDialog.DirectoryOnly)
    self.directoryDialog.setToolTip("The directory where the lumpnav data has been saved.")
    parametersFormLayout.addRow(self.directoryDialog)
    
    self.loadAllDataButton = qt.QPushButton("Load All Data")
    self.loadAllDataButton.setToolTip("Load the pertinent data for evaluating tumor tracking.")
    parametersFormLayout.addRow(self.loadAllDataButton)
    self.loadAllDataButton.connect('clicked()', self.onLoadAllDataButtonPressed)

    self.preprocessButton = qt.QPushButton("Preprocess")
    self.preprocessButton.setToolTip("Compute and record needle shaft coordinate system, update models.")
    parametersFormLayout.addRow(self.preprocessButton)
    self.preprocessButton.connect('clicked()', self.onPreprocessButtonPressed)

    self.changeToRecordingDataButton = qt.QPushButton("Change to Recording")
    self.changeToRecordingDataButton.setToolTip("Switch to Recording Data (preprocessing).")
    parametersFormLayout.addRow(self.changeToRecordingDataButton)
    self.changeToRecordingDataButton.connect('clicked()', self.onChangeToRecordingDataButtonPressed)

    self.changeToTrackingDataButton = qt.QPushButton("Change to Tracking")
    self.changeToTrackingDataButton.setToolTip("Switch to Tracking Data (evaluation).")
    parametersFormLayout.addRow(self.changeToTrackingDataButton)
    self.changeToTrackingDataButton.connect('clicked()', self.onChangeToTrackingDataButtonPressed)

    self.setupTumorTrackingButton = qt.QPushButton("Setup Tumor Tracking")
    self.setupTumorTrackingButton.setToolTip("Set up the tumor tracking nodes.")
    parametersFormLayout.addRow(self.setupTumorTrackingButton)
    self.setupTumorTrackingButton.connect('clicked()', self.onSetupTumorTrackingButtonPressed)

    self.computeColorMapButton = qt.QPushButton("Compute Color Map")
    self.computeColorMapButton.setToolTip("Compute the color map for distances between tumor models.")
    parametersFormLayout.addRow(self.computeColorMapButton)
    self.computeColorMapButton.connect('clicked()', self.onComputeColorMapButtonPressed)

    self.computeMetricsButton = qt.QPushButton("Compute Metrics")
    self.computeMetricsButton.setToolTip("Compute various metrics for evaluating and comparing tracking methods.")
    parametersFormLayout.addRow(self.computeMetricsButton)
    self.computeMetricsButton.connect('clicked()', self.onComputeMetricsButtonPressed)

    self.caseMetricCollectionButton = qt.QPushButton("Case metric collection")
    self.caseMetricCollectionButton.setToolTip("Begin automatic metric collection program for the loaded case.")
    parametersFormLayout.addRow(self.caseMetricCollectionButton)
    self.caseMetricCollectionButton.connect('clicked()', self.onCaseMetricCollectionButtonPressed)

    self.automaticMetricCollectionButton = qt.QPushButton("Automated metric collection")
    self.automaticMetricCollectionButton.setToolTip("Begin automatic metric collection for directories specified.")
    parametersFormLayout.addRow(self.automaticMetricCollectionButton)
    self.automaticMetricCollectionButton.connect('clicked()', self.onAutomaticMetricCollectionButtonPressed)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()
  
  def onLoadAllDataButtonPressed(self):
    self.logic.loadAllData(self.directoryDialog.text)

  def onPreprocessButtonPressed(self):
    self.logic.computeNeedleTransforms()
    self.logic.recordNeedleShaftRestingToReference()
    self.logic.updateTumorModels()

  def onSetupTumorTrackingButtonPressed(self):
    self.logic.setupTumorTracking()

  def onChangeToRecordingDataButtonPressed(self):
    self.logic.changeToRecordingData()

  def onChangeToTrackingDataButtonPressed(self):
    self.logic.changeToTrackingData()

  def onComputeColorMapButtonPressed(self):
    self.logic.computeComputeColorMap()

  def onComputeMetricsButtonPressed(self):
    self.logic.computeMetrics()

  def onCaseMetricCollectionButtonPressed(self):
    self.logic.beginCaseMetricComputation()

  def onAutomaticMetricCollectionButtonPressed(self):
    self.logic.beginAutomaticMetricComputation()

  def onShowColorMapButtonPressed(self):
    pass

  def onHideColorMapButtonPressed(self):
    pass
    
  def cleanup(self):
    pass

  def onSelect(self):
    pass

#
# TumorTrackingEvalLogic
#

class TumorTrackingEvalLogic(ScriptedLoadableModuleLogic):
    
  def loadAllData(self, tumorTrackingDirectory):
    self.tumorTrackingDirectory = tumorTrackingDirectory
    self.loadAllTransforms()
    self.loadRecordingSequences()
    self.loadTrackingSequences()
    self.loadAllModels()
    self.changeToRecordingData()

  def loadAllTransforms(self):
    logging.debug("loading transforms")

    # These are necessary for constructing visualizations
    self.referenceToRasNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "ReferenceToRas")
    self.cauteryTipToCauteryNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "CauteryTipToCautery")
    self.cauteryModelToCauteryTipNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "CauteryModelToCauteryTip")

    self.needleTipOriginalToNeedleNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "NeedleTipOriginalToNeedle")
    self.needleModelOriginalToNeedleTipOriginal = self.loadLinearTransformNode(self.tumorTrackingDirectory, "NeedleModelOriginalToNeedleTipOriginal")
    
    # These need to be calibrated, the values from surgery are not reliable
    self.needleTipToNeedleNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "NeedleTipToNeedle")
    self.needleShaftToNeedleTipNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "NeedleShaftToNeedleTip")
    # If markups have been defined, these can be used to define needleTipToNeedle and needleShaftToNeedleTip
    self.needleMarkupsNode_Needle = self.loadMarkupsNode(self.tumorTrackingDirectory, "NeedleMarkups_Needle")
    
    # For ultrasound images
    self.transducerToProbeNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, "TransducerToProbe")

    # For the transform fusion computation
    self.needleShaftRestingToReferenceNode = self.loadLinearTransformNode(self.tumorTrackingDirectory, 'NeedleShaftRestingToReference')

    # Results for tumor tracking
    self.tumor6dofToReferenceNode = self.initializeLinearTransformNode('Tumor6DOFToReference')
    self.tumor5dofToReferenceNode = self.initializeLinearTransformNode('Tumor5DOFToReference')
    self.tumor3dofToReferenceNode = self.initializeLinearTransformNode('Tumor3DOFToReference')

  def loadAllModels(self):
    logging.debug("loading models")

    self.removeExistingNodes("TumorModel*")

    # Tumor models need to be reloaded, even if they already exist in the scene
    slicer.util.loadModel(self.tumorTrackingDirectory + "TumorModel.vtk")
    self.tumorModelNode_Needle = slicer.util.getNode("TumorModel*")
    if (not self.tumorModelNode_Needle):
      logging.warning("No tumor model found. Using sphere as placeholder.")
      self.tumorModelNode_Needle = slicer.modules.createmodels.logic().CreateSphere(10.0)
      self.tumorModelNode_Needle=slicer.util.getNode(pattern="SphereModel")
    self.tumorModelNode_Needle.SetName("TumorModel_Needle")
    self.tumorModelNode_Needle.GetDisplayNode().SetColor(0.0, 1.0, 0.0)
    self.tumorModelNode_Needle.GetDisplayNode().SetOpacity(0.5)
    self.tumorModelNode_Needle.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.tumorModelNode_NeedleShaftResting = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(self.tumorModelNode_NeedleShaftResting)
    self.transformPolyDataNeedleToNeedleShaft(self.tumorModelNode_Needle,self.tumorModelNode_NeedleShaftResting)
    self.tumorModelNode_NeedleShaftResting.SetName("TumorModel_NeedleShaftResting")
    self.tumorModelNode_NeedleShaftResting.CreateDefaultDisplayNodes()
    self.tumorModelNode_NeedleShaftResting.GetDisplayNode().SetColor(0.5, 0.5, 0.5)
    self.tumorModelNode_NeedleShaftResting.GetDisplayNode().SliceIntersectionVisibilityOn()
    self.tumorModelNode_NeedleShaftResting.GetDisplayNode().SetVisibility(False)

    self.tumorModelNode_Tumor6dof = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(self.tumorModelNode_Tumor6dof)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor6dof)
    self.tumorModelNode_Tumor6dof.SetName("TumorModel_Tumor6DOF")
    self.tumorModelNode_Tumor6dof.CreateDefaultDisplayNodes()
    self.tumorModelNode_Tumor6dof.GetDisplayNode().SetColor(1.0, 0.5, 0.0)
    self.tumorModelNode_Tumor6dof.GetDisplayNode().SetOpacity(0.5)
    self.tumorModelNode_Tumor6dof.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.tumorModelNode_Tumor5dof = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(self.tumorModelNode_Tumor5dof)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor5dof)
    self.tumorModelNode_Tumor5dof.SetName("TumorModel_Tumor5DOF")
    self.tumorModelNode_Tumor5dof.CreateDefaultDisplayNodes()
    self.tumorModelNode_Tumor5dof.GetDisplayNode().SetColor(0.0, 0.5, 1.0)
    self.tumorModelNode_Tumor5dof.GetDisplayNode().SetOpacity(0.5)
    self.tumorModelNode_Tumor5dof.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.tumorModelNode_Tumor3dof = slicer.vtkMRMLModelNode()
    slicer.mrmlScene.AddNode(self.tumorModelNode_Tumor3dof)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor3dof)
    self.tumorModelNode_Tumor3dof.SetName("TumorModel_Tumor3DOF")
    self.tumorModelNode_Tumor3dof.CreateDefaultDisplayNodes()
    self.tumorModelNode_Tumor3dof.GetDisplayNode().SetColor(0.5, 0.0, 1.0)
    self.tumorModelNode_Tumor3dof.GetDisplayNode().SetOpacity(0.5)
    self.tumorModelNode_Tumor3dof.GetDisplayNode().SliceIntersectionVisibilityOn()

    # These models are constant, so it's okay to re-use these if they exist already
    self.cauteryModelNode_CauteryModel=slicer.util.getNode(pattern="CauteryModel_Cautery")
    if (not self.cauteryModelNode_CauteryModel):
      slicer.modules.createmodels.logic().CreateNeedle(60, 1.0, 0, 0)
      self.cauteryModelNode_CauteryModel=slicer.util.getNode(pattern="NeedleModel")
    self.cauteryModelNode_CauteryModel.SetName("CauteryModel_Cautery")
    self.cauteryModelNode_CauteryModel.GetDisplayNode().SetColor(1.0, 1.0, 0.0)
    self.cauteryModelNode_CauteryModel.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.needleModelNode_NeedleShaft=slicer.util.getNode(pattern="NeedleModel_NeedleShaft")
    if (not self.needleModelNode_NeedleShaft):
      slicer.modules.createmodels.logic().CreateNeedle(60, 1.0, 0, 0)
      self.needleModelNode_NeedleShaft=slicer.util.getNode(pattern="NeedleModel")
    self.needleModelNode_NeedleShaft.SetName("NeedleModel_NeedleShaft")
    self.needleModelNode_NeedleShaft.GetDisplayNode().SetColor(0.0, 1.0, 1.0)
    self.needleModelNode_NeedleShaft.GetDisplayNode().SliceIntersectionVisibilityOn()

    self.needleModelNode_NeedleModelOriginal=slicer.util.getNode(pattern="NeedleModel_NeedleModelOriginal")
    if (not self.needleModelNode_NeedleModelOriginal):
      slicer.modules.createmodels.logic().CreateNeedle(60, 1.0, 0, 0)
      self.needleModelNode_NeedleModelOriginal=slicer.util.getNode(pattern="NeedleModel")
    self.needleModelNode_NeedleModelOriginal.SetName("NeedleModel_NeedleModelOriginal")
    self.needleModelNode_NeedleModelOriginal.GetDisplayNode().SetColor(0.0, 0.5, 0.5)
    self.needleModelNode_NeedleModelOriginal.GetDisplayNode().SetOpacity(0.25)
    self.needleModelNode_NeedleModelOriginal.GetDisplayNode().SliceIntersectionVisibilityOn()

  def loadRecordingSequences(self):
    logging.debug("loading \'recording\' sequences")
    self.removeExistingNodes("recordingData*")
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':self.tumorTrackingDirectory+"recordingData.mha"})
    #slicer.vtkSlicerMetafileImporterLogic().ReadSequenceMetafile(self.tumorTrackingDirectory + "recordingData.mha")
    self.recordingData_trackerToReferenceNode = self.initializeLinearTransformNode("recordingData*-TrackerToReference")
    self.recordingData_needleToTrackerNode = self.initializeLinearTransformNode("recordingData*-NeedleToTracker")
    self.recordingData_cauteryToTrackerNode = self.initializeLinearTransformNode("recordingData*-CauteryToTracker")
    self.recordingData_sequenceBrowserNode = self.getSequenceBrowserNode('recordingData*')
    self.probeToTrackerNode = self.initializeLinearTransformNode("recordingData*-ProbeToTracker")
    self.imageToTransducerNode = self.initializeLinearTransformNode("recordingData*-ImageToTransducer")
    self.imageNode = getNode("recordingData*-Image")
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode

  def loadTrackingSequences(self):
    logging.debug("loading \'tracking\' sequences")
    self.removeExistingNodes("trackingData*")
    slicer.app.coreIOManager().loadNodes('Sequence Metafile',{'fileName':self.tumorTrackingDirectory+"trackingData.mha"})
    #slicer.vtkSlicerMetafileImporterLogic().ReadSequenceMetafile(self.tumorTrackingDirectory + "trackingData.mha")
    self.trackingData_trackerToReferenceNode = self.initializeLinearTransformNode("trackingData*-TrackerToReference")
    self.trackingData_needleToTrackerNode = self.initializeLinearTransformNode("trackingData*-NeedleToTracker")
    self.trackingData_cauteryToTrackerNode = self.initializeLinearTransformNode("trackingData*-CauteryToTracker")
    self.trackingData_sequenceBrowserNode = self.getSequenceBrowserNode('trackingData*')
    self.probeToTrackerNode = self.initializeLinearTransformNode("recordingData*-ProbeToTracker")
    self.imageToTransducerNode = self.initializeLinearTransformNode("recordingData*-ImageToTransducer")
    self.imageNode = getNode("recordingData*-Image")
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode

  def getSequenceBrowserNode(self, pattern):
    nodes = slicer.util.getNodes(pattern)
    keys = nodes.keys()
    for key in keys:
      if '-' not in key: # sequence browser node will not have a hyphen in its name, because it isn't in the filename
        return nodes[key]
    logging.error("No sequence browser node found for pattern: " + pattern)

  def transformPolyDataNeedleToNeedleShaft(self,sourceModelNode_Needle,targetModelNode_NeedleShaft):
    # All this below is to create a copy of the tumor model in the needle shaft coordinate system
    # The transform hiearchy does *not* need to be set up for this to work
    tumorPolygonData_NeedleShaft = vtk.vtkPolyData()
    tumorPolygonData_NeedleShaft.DeepCopy(sourceModelNode_Needle.GetPolyData())

    needleToNeedleTipTransform = vtk.vtkTransform()
    needleToNeedleTipTransform.DeepCopy(self.needleTipToNeedleNode.GetTransformToParent())
    needleToNeedleTipTransform.Inverse()
    needleToNeedleTipTransformFilter = vtk.vtkTransformFilter()
    needleToNeedleTipTransformFilter.SetTransform(needleToNeedleTipTransform)
    needleToNeedleTipTransformFilter.SetInputData(tumorPolygonData_NeedleShaft)
    needleToNeedleTipTransformFilter.Update()

    needleTipToNeedleShaftTransform = vtk.vtkTransform()
    needleTipToNeedleShaftTransform.DeepCopy(self.needleShaftToNeedleTipNode.GetTransformToParent())
    needleTipToNeedleShaftTransform.Inverse()
    needleTipToNeedleShaftTransformFilter = vtk.vtkTransformFilter()
    needleTipToNeedleShaftTransformFilter.SetTransform(needleTipToNeedleShaftTransform)
    needleTipToNeedleShaftTransformFilter.SetInputData(needleToNeedleTipTransformFilter.GetOutput())
    needleTipToNeedleShaftTransformFilter.Update()

    targetModelNode_NeedleShaft.SetAndObservePolyData(needleTipToNeedleShaftTransformFilter.GetOutput())
    targetModelNode_NeedleShaft.CreateDefaultDisplayNodes()

  def changeToRecordingData(self):
    self.trackerToReferenceNode = self.recordingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.recordingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.recordingData_needleToTrackerNode
    self.sequenceBrowserNode = self.recordingData_sequenceBrowserNode
    self.updateModelVisibility(inTrackingMode=False)
    self.setupTransformHierarchy()

  def changeToTrackingData(self):
    self.trackerToReferenceNode = self.trackingData_trackerToReferenceNode
    self.cauteryToTrackerNode = self.trackingData_cauteryToTrackerNode
    self.needleToTrackerNode = self.trackingData_needleToTrackerNode
    self.sequenceBrowserNode = self.trackingData_sequenceBrowserNode
    self.updateModelVisibility(inTrackingMode=True)
    self.setupTransformHierarchy()

  def updateModelVisibility(self, inTrackingMode=True):
    inRecordingMode = not inTrackingMode
    self.tumorModelNode_Needle.GetDisplayNode().SetVisibility(inRecordingMode)
    self.tumorModelNode_Tumor6dof.GetDisplayNode().SetVisibility(inTrackingMode)
    self.tumorModelNode_Tumor5dof.GetDisplayNode().SetVisibility(inTrackingMode)
    self.tumorModelNode_Tumor3dof.GetDisplayNode().SetVisibility(inTrackingMode)
    self.needleModelNode_NeedleModelOriginal.GetDisplayNode().SetVisibility(inRecordingMode)
    self.needleMarkupsNode_Needle.GetDisplayNode().SetVisibility(inRecordingMode)
    if self.imageNode:
      self.imageNode.GetDisplayNode().SetVisibility(inRecordingMode)

  def setupTransformHierarchy(self):
    logging.debug("setting up transform hierarchy")

    # reset all sequence nodes to the top of the transform hierarchy,
    # only those in the changeToXXXData will be used
    self.recordingData_trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.recordingData_needleToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.recordingData_cauteryToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.trackingData_trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.trackingData_needleToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.trackingData_cauteryToTrackerNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())

    self.trackerToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.cauteryToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.cauteryTipToCauteryNode.SetAndObserveTransformNodeID(self.cauteryToTrackerNode.GetID())
    self.cauteryModelToCauteryTipNode.SetAndObserveTransformNodeID(self.cauteryTipToCauteryNode.GetID())
    self.cauteryModelNode_CauteryModel.SetAndObserveTransformNodeID(self.cauteryModelToCauteryTipNode.GetID())
    
    self.needleToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.needleTipOriginalToNeedleNode.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())
    self.needleModelOriginalToNeedleTipOriginal.SetAndObserveTransformNodeID(self.needleTipOriginalToNeedleNode.GetID())
    self.needleModelNode_NeedleModelOriginal.SetAndObserveTransformNodeID(self.needleModelOriginalToNeedleTipOriginal.GetID())
    self.tumorModelNode_Needle.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())
    self.needleMarkupsNode_Needle.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())
    self.needleTipToNeedleNode.SetAndObserveTransformNodeID(self.needleToTrackerNode.GetID())
    self.needleShaftToNeedleTipNode.SetAndObserveTransformNodeID(self.needleTipToNeedleNode.GetID())
    self.needleModelNode_NeedleShaft.SetAndObserveTransformNodeID(self.needleShaftToNeedleTipNode.GetID())

    self.probeToTrackerNode.SetAndObserveTransformNodeID(self.trackerToReferenceNode.GetID())
    self.transducerToProbeNode.SetAndObserveTransformNodeID(self.probeToTrackerNode.GetID())
    self.imageToTransducerNode.SetAndObserveTransformNodeID(self.transducerToProbeNode.GetID())
    if self.imageNode:
      self.imageNode.SetAndObserveTransformNodeID(self.imageToTransducerNode.GetID())

    self.needleShaftRestingToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.tumorModelNode_NeedleShaftResting.SetAndObserveTransformNodeID(self.needleShaftRestingToReferenceNode.GetID())
    self.tumor6dofToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.tumorModelNode_Tumor6dof.SetAndObserveTransformNodeID(self.tumor6dofToReferenceNode.GetID())
    self.tumor5dofToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.tumorModelNode_Tumor5dof.SetAndObserveTransformNodeID(self.tumor5dofToReferenceNode.GetID())
    self.tumor3dofToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())
    self.tumorModelNode_Tumor3dof.SetAndObserveTransformNodeID(self.tumor3dofToReferenceNode.GetID())

  def computeNeedleTransforms(self):
    if (self.needleMarkupsNode_Needle.GetNumberOfMarkups() < 2):
      logging.error("Inusfficient number of markups to compute needle transforms")
    needleTipPoint_Needle = [0,0,0]
    self.needleMarkupsNode_Needle.GetNthFiducialPosition(0, needleTipPoint_Needle)
    needleShaftPoint_Needle = [0,0,0]
    self.needleMarkupsNode_Needle.GetNthFiducialPosition(1, needleShaftPoint_Needle)
    needleShaftDirection_Needle = [0,0,0]
    vtk.vtkMath.Subtract(needleTipPoint_Needle, needleShaftPoint_Needle, needleShaftDirection_Needle)
    vtk.vtkMath.Normalize(needleShaftDirection_Needle)
    needleShaftXAxis_Needle = [0,0,0]
    needleShaftYAxis_Needle = [0,0,0]
    needleShaftZAxis_Needle = needleShaftDirection_Needle
    vtk.vtkMath.Perpendiculars(needleShaftZAxis_Needle, needleShaftXAxis_Needle, needleShaftYAxis_Needle, 0)
    needleShaftMatrix_Needle = vtk.vtkMatrix4x4()
    needleShaftMatrix_Needle.SetElement(0, 0, needleShaftXAxis_Needle[0])
    needleShaftMatrix_Needle.SetElement(1, 0, needleShaftXAxis_Needle[1])
    needleShaftMatrix_Needle.SetElement(2, 0, needleShaftXAxis_Needle[2])
    needleShaftMatrix_Needle.SetElement(0, 1, needleShaftYAxis_Needle[0])
    needleShaftMatrix_Needle.SetElement(1, 1, needleShaftYAxis_Needle[1])
    needleShaftMatrix_Needle.SetElement(2, 1, needleShaftYAxis_Needle[2])
    needleShaftMatrix_Needle.SetElement(0, 2, needleShaftZAxis_Needle[0])
    needleShaftMatrix_Needle.SetElement(1, 2, needleShaftZAxis_Needle[1])
    needleShaftMatrix_Needle.SetElement(2, 2, needleShaftZAxis_Needle[2])
    # TODO: Replace the above code with the function from TransformFusionLogic: GetRotationMatrixFromAxes()
    self.needleShaftToNeedleTipNode.SetMatrixTransformToParent(needleShaftMatrix_Needle)
    needleTipMatrix_Needle = vtk.vtkMatrix4x4()
    needleTipMatrix_Needle.SetElement(0, 3, needleTipPoint_Needle[0])
    needleTipMatrix_Needle.SetElement(1, 3, needleTipPoint_Needle[1])
    needleTipMatrix_Needle.SetElement(2, 3, needleTipPoint_Needle[2])
    self.needleTipToNeedleNode.SetMatrixTransformToParent(needleTipMatrix_Needle)

  def updateTumorModels(self):
    self.transformPolyDataNeedleToNeedleShaft(self.tumorModelNode_Needle, self.tumorModelNode_NeedleShaftResting)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor6dof)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor5dof)
    self.copyPolyDataFromSourceToTargetModelNode(self.tumorModelNode_NeedleShaftResting, self.tumorModelNode_Tumor3dof)

  def recordNeedleShaftRestingToReference(self):
    if not self.referenceToRasNode:
      logging.error("No referenceToRasNode!")
      return
    if not self.needleShaftToNeedleTipNode:
      logging.error("No needleShaftToNeedleTipNode!")
      return
    if not self.needleShaftRestingToReferenceNode:
      logging.error("No needleShaftRestingToReferenceNode!")
      return
    logging.debug('recordNeedleShaftRestingToReference')
    needleShaftToReferenceGeneralTransform = vtk.vtkGeneralTransform()
    self.needleShaftToNeedleTipNode.GetTransformToNode(self.referenceToRasNode,needleShaftToReferenceGeneralTransform)
    needleShaftToReferenceLinearTransform = vtk.vtkTransform()
    self.computeLinearTransformFromGeneralTransform(needleShaftToReferenceGeneralTransform, needleShaftToReferenceLinearTransform)
    self.needleShaftRestingToReferenceNode.SetAndObserveTransformToParent(needleShaftToReferenceLinearTransform)
    self.needleShaftRestingToReferenceNode.SetAndObserveTransformNodeID(self.referenceToRasNode.GetID())

  def computeLinearTransformFromGeneralTransform(self, generalTransform, linearTransform):
    xAxis = generalTransform.TransformVectorAtPoint([0,0,0],[1,0,0])
    yAxis = generalTransform.TransformVectorAtPoint([0,0,0],[0,1,0])
    zAxis = generalTransform.TransformVectorAtPoint([0,0,0],[0,0,1])
    translation = generalTransform.TransformPoint([0,0,0])
    matrix = vtk.vtkMatrix4x4()
    matrix.Identity()
    matrix.SetElement(0, 0, xAxis[0])
    matrix.SetElement(0, 1, yAxis[0])
    matrix.SetElement(0, 2, zAxis[0])
    matrix.SetElement(0, 3, translation[0])
    matrix.SetElement(1, 0, xAxis[1])
    matrix.SetElement(1, 1, yAxis[1])
    matrix.SetElement(1, 2, zAxis[1])
    matrix.SetElement(1, 3, translation[1])
    matrix.SetElement(2, 0, xAxis[2])
    matrix.SetElement(2, 1, yAxis[2])
    matrix.SetElement(2, 2, zAxis[2])
    matrix.SetElement(2, 3, translation[2])
    linearTransform.SetMatrix(matrix)

  def setupTumorTracking(self):
    logging.debug('setupTumorTracking')

    self.tumor6dofTransformFusionNode = slicer.util.getNode("Tumor6dofTransformFusionNode")
    if not self.tumor6dofTransformFusionNode:
      self.tumor6dofTransformFusionNode = slicer.vtkMRMLTransformFusionNode()
      slicer.mrmlScene.AddNode(self.tumor6dofTransformFusionNode)
      self.tumor6dofTransformFusionNode.SetName("Tumor6dofTransformFusionNode")
    self.tumor6dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_MANUAL) # To temporarily prevent warnings
    self.tumor6dofTransformFusionNode.SetFusionMode(slicer.vtkMRMLTransformFusionNode.FUSION_MODE_COPY_FULL_TRANSFORM)
    self.tumor6dofTransformFusionNode.SetAndObserveSingleSourceTransformNode(self.needleShaftToNeedleTipNode)
    self.tumor6dofTransformFusionNode.SetAndObserveReferenceTransformNode(self.referenceToRasNode)
    self.tumor6dofTransformFusionNode.SetAndObserveResultTransformNode(self.tumor6dofToReferenceNode)
    self.tumor6dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_AUTO)

    self.tumor5dofTransformFusionNode = slicer.util.getNode("Tumor5dofTransformFusionNode")
    if not self.tumor5dofTransformFusionNode:
      self.tumor5dofTransformFusionNode = slicer.vtkMRMLTransformFusionNode()
      slicer.mrmlScene.AddNode(self.tumor5dofTransformFusionNode)
      self.tumor5dofTransformFusionNode.SetName("Tumor5dofTransformFusionNode")
    self.tumor5dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_MANUAL) # To temporarily prevent warnings
    self.tumor5dofTransformFusionNode.SetFusionMode(slicer.vtkMRMLTransformFusionNode.FUSION_MODE_CONSTRAIN_SHAFT_ROTATION)
    self.tumor5dofTransformFusionNode.SetAndObserveSingleSourceTransformNode(self.needleShaftToNeedleTipNode)
    self.tumor5dofTransformFusionNode.SetAndObserveReferenceTransformNode(self.referenceToRasNode)
    self.tumor5dofTransformFusionNode.SetAndObserveTargetTransformNode(self.needleShaftRestingToReferenceNode)
    self.tumor5dofTransformFusionNode.SetAndObserveResultTransformNode(self.tumor5dofToReferenceNode)
    self.tumor5dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_AUTO)

    self.tumor3dofTransformFusionNode = slicer.util.getNode("Tumor3dofTransformFusionNode")
    if not self.tumor3dofTransformFusionNode:
      self.tumor3dofTransformFusionNode = slicer.vtkMRMLTransformFusionNode()
      slicer.mrmlScene.AddNode(self.tumor3dofTransformFusionNode)
      self.tumor3dofTransformFusionNode.SetName("Tumor3dofTransformFusionNode")
    self.tumor3dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_MANUAL) # To temporarily prevent warnings
    self.tumor3dofTransformFusionNode.SetFusionMode(slicer.vtkMRMLTransformFusionNode.FUSION_MODE_CONSTRAIN_ALL_ROTATION)
    self.tumor3dofTransformFusionNode.SetAndObserveSingleSourceTransformNode(self.needleShaftToNeedleTipNode)
    self.tumor3dofTransformFusionNode.SetAndObserveReferenceTransformNode(self.referenceToRasNode)
    self.tumor3dofTransformFusionNode.SetAndObserveTargetTransformNode(self.needleShaftRestingToReferenceNode)
    self.tumor3dofTransformFusionNode.SetAndObserveResultTransformNode(self.tumor3dofToReferenceNode)
    self.tumor3dofTransformFusionNode.SetUpdateMode(slicer.vtkMRMLTransformFusionNode.UPDATE_MODE_AUTO)

  def computeComputeColorMap(self):
    tumorPolyData = self.tumorModelNode_NeedleShaftResting.GetPolyData()

    tumor6dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor6dofToReferenceNode,tumorPolyData,tumor6dofPolyData)

    tumor5dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor5dofToReferenceNode,tumorPolyData,tumor5dofPolyData)

    distances5dofTo6dof = vtk.vtkDoubleArray()
    self.computeShortestDistances(tumor5dofPolyData, tumor6dofPolyData, distances5dofTo6dof)
    distances5dofTo6dof.SetName("distances5dofTo6dof")
    self.tumorModelNode_Tumor5dof.AddPointScalars(distances5dofTo6dof)

    tumor3dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor3dofToReferenceNode,tumorPolyData,tumor3dofPolyData)

    distances3dofTo6dof = vtk.vtkDoubleArray()
    self.computeShortestDistances(tumor3dofPolyData, tumor6dofPolyData, distances3dofTo6dof)
    distances3dofTo6dof.SetName("distances3dofTo6dof")
    self.tumorModelNode_Tumor3dof.AddPointScalars(distances3dofTo6dof)

  def initializeMetrics(self):
    self.metricsTable = slicer.util.getNode("MetricsTable")
    if self.metricsTable:
      self.metricsTable.RemoveAllColumns()
    else:
      self.metricsTable = slicer.vtkMRMLTableNode()
      self.metricsTable.SetName("MetricsTable")
      slicer.mrmlScene.AddNode(self.metricsTable)

    self.labelFrameIndex = 'frameIndex'
    self.labelTime = 'timeSeconds'
    self.labelSurfaceDistance5dof6dofMean = 'surfaceDistance5dof6dofMeanMm'
    self.labelSurfaceDistance5dof6dofPercentile000 = 'surfaceDistance5dof6dofPercentile000Mm'
    self.labelSurfaceDistance5dof6dofPercentile005 = 'surfaceDistance5dof6dofPercentile005Mm'
    self.labelSurfaceDistance5dof6dofPercentile032 = 'surfaceDistance5dof6dofPercentile032Mm'
    self.labelSurfaceDistance5dof6dofPercentile050 = 'surfaceDistance5dof6dofPercentile050Mm'
    self.labelSurfaceDistance5dof6dofPercentile068 = 'surfaceDistance5dof6dofPercentile068Mm'
    self.labelSurfaceDistance5dof6dofPercentile095 = 'surfaceDistance5dof6dofPercentile095Mm'
    self.labelSurfaceDistance5dof6dofPercentile100 = 'surfaceDistance5dof6dofPercentile100Mm'
    self.labelSurfaceDistance3dof6dofMean = 'surfaceDistance3dof6dofMeanMm'
    self.labelSurfaceDistance3dof6dofPercentile000 = 'surfaceDistance3dof6dofPercentile000Mm'
    self.labelSurfaceDistance3dof6dofPercentile005 = 'surfaceDistance3dof6dofPercentile005Mm'
    self.labelSurfaceDistance3dof6dofPercentile032 = 'surfaceDistance3dof6dofPercentile032Mm'
    self.labelSurfaceDistance3dof6dofPercentile050 = 'surfaceDistance3dof6dofPercentile050Mm'
    self.labelSurfaceDistance3dof6dofPercentile068 = 'surfaceDistance3dof6dofPercentile068Mm'
    self.labelSurfaceDistance3dof6dofPercentile095 = 'surfaceDistance3dof6dofPercentile095Mm'
    self.labelSurfaceDistance3dof6dofPercentile100 = 'surfaceDistance3dof6dofPercentile100Mm'
    self.labelVolume6dof = 'volumeTumor6dofMm3'
    self.labelVolume5dof = 'volumeTumor5dofMm3'
    self.labelVolume3dof = 'volumeTumor3dofMm3'
    self.labelVolumeIntersection5dof6dof = 'volumeIntersection5dof6dofMm3'
    self.labelVolumeIntersection3dof6dof = 'volumeIntersection3dof6dofMm3'
    self.labelTransformDifferenceTipCurrentToResting = 'transformDifferenceTipCurrentToRestingMm'
    self.labelTransformDifference6dofToRestingSpinAroundX = 'transformDifferenceZAxis6dofToRestingSpinXDeg'
    self.labelTransformDifference6dofToRestingSpinAroundY = 'transformDifferenceZAxis6dofToRestingSpinYDeg'
    self.labelTransformDifference6dofToRestingLiftZAxis = 'transformDifferenceZAxis6dofToRestingLiftDeg'
    self.labelTransformDifference6dofToRestingOverallAngle = 'transformDifferenceOverallAngle6dofToRestingDeg'
    self.labelTransformDifference5dofToRestingSpinAroundX = 'transformDifferenceZAxis5dofToRestingSpinXDeg'
    self.labelTransformDifference5dofToRestingSpinAroundY = 'transformDifferenceZAxis5dofToRestingSpinYDeg'
    self.labelTransformDifference5dofToRestingLiftZAxis = 'transformDifferenceZAxis5dofToRestingLiftDeg'
    self.labelTransformDifference5dofToRestingOverallAngle = 'transformDifferenceOverallAngle5dofToRestingDeg'
    self.labelTransformDifference3dofToRestingSpinAroundX = 'transformDifferenceZAxis3dofToRestingSpinXDeg'
    self.labelTransformDifference3dofToRestingSpinAroundY = 'transformDifferenceZAxis3dofToRestingSpinYDeg'
    self.labelTransformDifference3dofToRestingLiftZAxis = 'transformDifferenceZAxis3dofToRestingLiftDeg'
    self.labelTransformDifference3dofToRestingOverallAngle = 'transformDifferenceOverallAngle3dofToRestingDeg'
    self.labelCauteryTipDistanceTo6dof = 'cauteryTipDistanceTo6dofMm'
    self.labelCauteryTipDistanceTo5dof = 'cauteryTipDistanceTo5dofMm'
    self.labelCauteryTipDistanceTo3dof = 'cauteryTipDistanceTo3dofMm'
    self.labelCauteryTipDistanceToResting = 'cauteryTipDistanceToRestingMm'

    self.metricList = \
      [
        self.labelFrameIndex,
        self.labelTime,
        self.labelSurfaceDistance5dof6dofMean,
        self.labelSurfaceDistance5dof6dofPercentile000,
        self.labelSurfaceDistance5dof6dofPercentile005,
        self.labelSurfaceDistance5dof6dofPercentile032,
        self.labelSurfaceDistance5dof6dofPercentile050,
        self.labelSurfaceDistance5dof6dofPercentile068,
        self.labelSurfaceDistance5dof6dofPercentile095,
        self.labelSurfaceDistance5dof6dofPercentile100,
        self.labelSurfaceDistance3dof6dofMean,
        self.labelSurfaceDistance3dof6dofPercentile000,
        self.labelSurfaceDistance3dof6dofPercentile005,
        self.labelSurfaceDistance3dof6dofPercentile032,
        self.labelSurfaceDistance3dof6dofPercentile050,
        self.labelSurfaceDistance3dof6dofPercentile068,
        self.labelSurfaceDistance3dof6dofPercentile095,
        self.labelSurfaceDistance3dof6dofPercentile100,
        self.labelVolume6dof,
        self.labelVolume5dof,
        self.labelVolume3dof,
        self.labelVolumeIntersection5dof6dof,
        self.labelVolumeIntersection3dof6dof,
        self.labelTransformDifferenceTipCurrentToResting,
        self.labelTransformDifference6dofToRestingSpinAroundX,
        self.labelTransformDifference6dofToRestingSpinAroundY,
        self.labelTransformDifference6dofToRestingLiftZAxis,
        self.labelTransformDifference6dofToRestingOverallAngle,
        self.labelTransformDifference5dofToRestingSpinAroundX,
        self.labelTransformDifference5dofToRestingSpinAroundY,
        self.labelTransformDifference5dofToRestingLiftZAxis,
        self.labelTransformDifference5dofToRestingOverallAngle,
        self.labelTransformDifference3dofToRestingSpinAroundX,
        self.labelTransformDifference3dofToRestingSpinAroundY,
        self.labelTransformDifference3dofToRestingLiftZAxis,
        self.labelTransformDifference3dofToRestingOverallAngle,
        self.labelCauteryTipDistanceTo6dof,
        self.labelCauteryTipDistanceTo5dof,
        self.labelCauteryTipDistanceTo3dof,
        self.labelCauteryTipDistanceToResting
      ]

    tableFirstColumn = vtk.vtkStringArray()
    for label in self.metricList:
      tableFirstColumn.InsertNextValue(label)
    self.metricsTable.AddColumn(tableFirstColumn)

    self.labelSurfaceDistance5dof6dofPercentileBase = 'surfaceDistance5dof6dofPercentile'
    self.labelSurfaceDistance3dof6dofPercentileBase = 'surfaceDistance3dof6dofPercentile'

  def computeMetrics(self):
    self.metricsTable = slicer.util.getNode("MetricsTable")
    if not self.metricsTable:
      self.initializeMetrics()

    metricList = self.metricList
    numberOfMetrics = len(metricList)
    metricsArray = vtk.vtkDoubleArray()
    metricsArray.SetNumberOfComponents(1)
    metricsArray.SetNumberOfTuples(numberOfMetrics)

    self.addGeneralInfoToMetrics(self.labelFrameIndex, self.labelTime, metricList, metricsArray)

    # Compute some general-use variables
    tumorPolyData = self.tumorModelNode_NeedleShaftResting.GetPolyData()
    tumorRestingPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.needleShaftRestingToReferenceNode, tumorPolyData, tumorRestingPolyData)
    tumor6dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor6dofToReferenceNode, tumorPolyData, tumor6dofPolyData)
    tumor5dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor5dofToReferenceNode, tumorPolyData, tumor5dofPolyData)
    tumor3dofPolyData = vtk.vtkPolyData()
    self.applyTransformNodeToPolyData(self.tumor3dofToReferenceNode, tumorPolyData, tumor3dofPolyData)

    self.computeDistanceMetrics(tumor5dofPolyData, tumor6dofPolyData,
                                self.labelSurfaceDistance5dof6dofMean,
                                self.labelSurfaceDistance5dof6dofPercentileBase,
                                metricList, metricsArray)
    self.computeDistanceMetrics(tumor3dofPolyData, tumor6dofPolyData,
                                self.labelSurfaceDistance3dof6dofMean,
                                self.labelSurfaceDistance3dof6dofPercentileBase,
                                metricList, metricsArray)
    self.computeVolumeCompareMetrics(tumor5dofPolyData, tumor6dofPolyData,
                                     self.labelVolume5dof,
                                     self.labelVolume6dof,
                                     self.labelVolumeIntersection5dof6dof,
                                     metricList, metricsArray)
    self.computeVolumeCompareMetrics(tumor3dofPolyData, tumor6dofPolyData,
                                     self.labelVolume3dof,
                                     None, # already computed
                                     self.labelVolumeIntersection3dof6dof,
                                     metricList, metricsArray)
    self.computeTransformMetrics(self.tumor6dofToReferenceNode, self.needleShaftRestingToReferenceNode,
                                 self.labelTransformDifferenceTipCurrentToResting,
                                 self.labelTransformDifference6dofToRestingSpinAroundX,
                                 self.labelTransformDifference6dofToRestingSpinAroundY,
                                 self.labelTransformDifference6dofToRestingLiftZAxis,
                                 self.labelTransformDifference6dofToRestingOverallAngle,
                                 metricList, metricsArray)
    self.computeTransformMetrics(self.tumor5dofToReferenceNode, self.needleShaftRestingToReferenceNode,
                                 None,
                                 self.labelTransformDifference5dofToRestingSpinAroundX,
                                 self.labelTransformDifference5dofToRestingSpinAroundY,
                                 self.labelTransformDifference5dofToRestingLiftZAxis,
                                 self.labelTransformDifference5dofToRestingOverallAngle,
                                 metricList, metricsArray)
    self.computeTransformMetrics(self.tumor3dofToReferenceNode, self.needleShaftRestingToReferenceNode,
                                 None,
                                 self.labelTransformDifference3dofToRestingSpinAroundX,
                                 self.labelTransformDifference3dofToRestingSpinAroundY,
                                 self.labelTransformDifference3dofToRestingLiftZAxis,
                                 self.labelTransformDifference3dofToRestingOverallAngle,
                                 metricList, metricsArray)

    # Find cautery tip
    cauteryTipToReferenceTransform = vtk.vtkGeneralTransform()
    self.cauteryTipToCauteryNode.GetTransformToNode(self.referenceToRasNode, cauteryTipToReferenceTransform)
    cauteryTip_Reference = cauteryTipToReferenceTransform.TransformPoint([0,0,0])
    self.computeCauteryTipMetrics(cauteryTip_Reference, tumor6dofPolyData, self.labelCauteryTipDistanceTo6dof,
                                  metricList, metricsArray)
    self.computeCauteryTipMetrics(cauteryTip_Reference, tumor5dofPolyData, self.labelCauteryTipDistanceTo5dof,
                                  metricList, metricsArray)
    self.computeCauteryTipMetrics(cauteryTip_Reference, tumor3dofPolyData, self.labelCauteryTipDistanceTo3dof,
                                  metricList, metricsArray)
    self.computeCauteryTipMetrics(cauteryTip_Reference, tumorRestingPolyData, self.labelCauteryTipDistanceToResting,
                                  metricList, metricsArray)

    self.metricsTable.AddColumn(metricsArray)

  def applyTransformNodeToPolyData(self, transformNode, inputPolyData, outputPolyData):
    transform = transformNode.GetTransformToParent()
    transformFilter = vtk.vtkTransformFilter()
    transformFilter.SetTransform(transform)
    transformFilter.SetInputData(inputPolyData)
    transformFilter.Update()
    outputPolyData.DeepCopy(transformFilter.GetOutput())

  def computePairwiseDistances(self, sourcePolyData, referencePolyData, outputDistances):
    sourcePoints = sourcePolyData.GetPoints()
    referencePoints = referencePolyData.GetPoints()
    numberOfPoints = sourcePoints.GetNumberOfPoints()
    if referencePoints.GetNumberOfPoints() != numberOfPoints:
      logging.error("Poly data have different numbers of points! Cannot compute distance map")
      return
    outputDistances.SetNumberOfComponents(1)
    outputDistances.SetNumberOfTuples(numberOfPoints)
    vtkMath = vtk.vtkMath()
    for i in xrange(0,numberOfPoints):
      sourcePoint = sourcePoints.GetPoint(i)
      referencePoint = referencePoints.GetPoint(i)
      distance = numpy.sqrt(vtkMath.Distance2BetweenPoints(sourcePoint, referencePoint))
      outputDistances.SetTuple1(i, distance)

  def computeShortestDistances(self, sourcePolyData, referencePolyData, outputDistances):
    import vtkSlicerSegmentComparisonModuleLogicPython
    distanceFilter = vtkSlicerSegmentComparisonModuleLogicPython.vtkPolyDataDistanceHistogramFilter()
    distanceFilter.SetInputComparePolyData(sourcePolyData)
    distanceFilter.SetInputReferencePolyData(referencePolyData)
    distanceFilter.Update()
    outputDistances.DeepCopy(distanceFilter.GetOutputDistances())

  def addGeneralInfoToMetrics(self, labelFrame, labelTime, metricList, outputMetricsArray):
    # need to store the sequence browser node somewhere
    frameIndex = self.sequenceBrowserNode.GetSelectedItemNumber()
    if labelFrame and labelFrame in metricList:
      arrayIndex = metricList.index(labelFrame)
      outputMetricsArray.SetTuple1(arrayIndex, frameIndex)

    timeSeconds = float(self.sequenceBrowserNode.GetMasterSequenceNode().GetNthIndexValue(frameIndex))
    if labelTime and labelTime in metricList:
      arrayIndex = metricList.index(labelTime)
      outputMetricsArray.SetTuple1(arrayIndex, timeSeconds)

  def computeDistanceMetrics(self, sourcePolyData, referencePolyData,
                             labelSurfaceDistanceMean,
                             labelSurfaceDistancePercentileBase,
                             metricList, outputMetricsArray):
    import vtkSlicerSegmentComparisonModuleLogicPython
    distanceFilter = vtkSlicerSegmentComparisonModuleLogicPython.vtkPolyDataDistanceHistogramFilter()
    distanceFilter.SetInputComparePolyData(sourcePolyData)
    distanceFilter.SetInputReferencePolyData(referencePolyData)
    distanceFilter.Update()

    # Mean distance
    if labelSurfaceDistanceMean and labelSurfaceDistanceMean in metricList:
      arrayIndex = metricList.index(labelSurfaceDistanceMean)
      outputMetricsArray.SetTuple1(arrayIndex, distanceFilter.GetAverageHausdorffDistance())

    # Percentiles
    if labelSurfaceDistancePercentileBase:
      for n in xrange(0,101): # check for anything in the range 0..100 inclusive
        label = labelSurfaceDistancePercentileBase + str('{:03d}'.format(n)) + "Mm"
        if label in metricList:
          arrayIndex = metricList.index(label)
          outputMetricsArray.SetTuple1(arrayIndex, distanceFilter.GetNthPercentileHausdorffDistance(n))

  def computeVolumeMetrics(self, polyData, labelVolume, metricList, outputMetricsArray):
    if labelVolume and labelVolume in metricList:
      massPropertiesFilter = vtk.vtkMassProperties()
      massPropertiesFilter.SetInputData(polyData)
      massPropertiesFilter.Update()
      arrayIndex = metricList.index(labelVolume)
      outputMetricsArray.SetTuple1(arrayIndex, massPropertiesFilter.GetVolume())

  def computeVolumeCompareMetrics(self, sourcePolyData, referencePolyData,
                                  labelVolumeSource,
                                  labelVolumeReference,
                                  labelVolumeIntersection,
                                  metricList, outputMetricsArray):
    import vtkSegmentationCorePython as vtkSegmentationCore

    segmentationNodeName = 'TumorTrackingEvalSegmentationNode'
    segmentationNode = slicer.util.getNode(segmentationNodeName)
    if not segmentationNode:
      segmentationNode = slicer.vtkMRMLSegmentationNode()
      slicer.mrmlScene.AddNode(segmentationNode)
      segmentationNode.CreateDefaultDisplayNodes()
      segmentationNode.SetName(segmentationNodeName)

    commonLabelmap = vtkSegmentationCore.vtkOrientedImageData()
    commonLabelmap.SetSpacing(0.5, 0.5, 0.5)
    commonLabelmap.SetExtent(0, 1, 0, 1, 0, 1)
    commonGeometryString = vtkSegmentationCore.vtkSegmentationConverter.SerializeImageGeometry(commonLabelmap)
    segmentationNode.GetSegmentation().SetConversionParameter(vtkSegmentationCore.vtkSegmentationConverter.GetReferenceImageGeometryParameterName(), commonGeometryString)

    sourceSegment = vtkSegmentationCore.vtkSegment()
    sourceSegment.SetName("Source")
    sourceSegment.SetColor(1.0,0.0,0.0)
    sourceSegment.AddRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName(), sourcePolyData)
    segmentationNode.GetSegmentation().AddSegment(sourceSegment)

    referenceSegment = vtkSegmentationCore.vtkSegment()
    referenceSegment.SetName("Reference")
    referenceSegment.SetColor(0.0, 0.0, 1.0)
    referenceSegment.AddRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName(), referencePolyData)
    segmentationNode.GetSegmentation().AddSegment(referenceSegment)

    segmentationNode.GetSegmentation().CreateRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())

    sourceLabelmap = sourceSegment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    referenceLabelmap = referenceSegment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
    intersectionLabelmap = vtkSegmentationCore.vtkOrientedImageData()
    vtkSegmentationCore.vtkOrientedImageDataResample.MergeImage(sourceLabelmap, referenceLabelmap, intersectionLabelmap, vtkSegmentationCore.vtkOrientedImageDataResample.OPERATION_MINIMUM)

    intersectionSegment = vtkSegmentationCore.vtkSegment()
    intersectionSegment.SetName("Intersection")
    intersectionSegment.SetColor(0.0,1.0,0.0)
    intersectionSegment.AddRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName(), intersectionLabelmap)
    segmentationNode.GetSegmentation().AddSegment(intersectionSegment)

    segmentationNode.GetSegmentation().CreateRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())

    if labelVolumeSource:
      sourceSegmentPolyData = sourceSegment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())
      self.computeVolumeMetrics(sourceSegmentPolyData,labelVolumeSource, metricList, outputMetricsArray)
    if labelVolumeReference:
      referenceSegmentPolyData = referenceSegment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())
      self.computeVolumeMetrics(referenceSegmentPolyData,labelVolumeReference, metricList, outputMetricsArray)
    if labelVolumeIntersection:
      intersectionSegmentPolyData = intersectionSegment.GetRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName())
      self.computeVolumeMetrics(intersectionSegmentPolyData,labelVolumeIntersection, metricList, outputMetricsArray)

    segmentationNode.GetSegmentation().RemoveSegment(sourceSegment)
    segmentationNode.GetSegmentation().RemoveSegment(referenceSegment)
    segmentationNode.GetSegmentation().RemoveSegment(intersectionSegment)

  def computeTransformMetrics(self, sourceTransformNode, referenceTransformNode,
                              labelTransformDifferencePosition,
                              labelTransformSpinAroundZAxisXComponent,
                              labelTransformSpinAroundZAxisYComponent,
                              labelTransformDifferenceZAxis,
                              labelTransformDifferenceOverallAngle,
                              metricList, outputMetricsArray):
    sourceToReferenceGeneralTransform = vtk.vtkGeneralTransform()
    zeroVector = [0, 0, 0]
    sourceTransformNode.GetTransformToNode(referenceTransformNode, sourceToReferenceGeneralTransform)
    sourceToReferenceTransform = vtk.vtkTransform() # linear transform
    self.computeLinearTransformFromGeneralTransform(sourceToReferenceGeneralTransform, sourceToReferenceTransform)
    sourceToReferenceTranslation = sourceToReferenceTransform.TransformDoublePoint(zeroVector)
    if labelTransformDifferencePosition and labelTransformDifferencePosition in metricList:
      transformDifferencePositionMm = numpy.linalg.norm(sourceToReferenceTranslation)
      arrayIndex = metricList.index(labelTransformDifferencePosition)
      outputMetricsArray.SetTuple1(arrayIndex, transformDifferencePositionMm)

    zAxis = [0, 0, 1]
    sourceToReferenceZAxis = sourceToReferenceTransform.TransformVectorAtPoint(zeroVector, zAxis)
    traceElement = sourceToReferenceZAxis[2]
    if traceElement > 1:
      traceElement = 1
    if traceElement < -1:
      traceElement = -1
    transformDifferenceZAxisDeg = numpy.arccos(traceElement) / numpy.pi * 180
    if labelTransformDifferenceZAxis and labelTransformDifferenceZAxis in metricList:
      arrayIndex = metricList.index(labelTransformDifferenceZAxis)
      outputMetricsArray.SetTuple1(arrayIndex, transformDifferenceZAxisDeg)

    # compute a rotation to bring the z axis back, so we can reliably compute the rotation around z
    angle_source = transformDifferenceZAxisDeg
    axis_reference = [0,0,0]
    # z will remain zero, but x and y need to be computed
    # the axis will be perpendicular to the direction of rotation,
    # so simply take the x and y components of the z axis and compute
    # a normalized orthogonal vector to those (rotate 90 degrees in-plane)
    xComponentOfZAxis = sourceToReferenceZAxis[0]
    yComponentOfZAxis = sourceToReferenceZAxis[1]
    axis_reference[0] = -yComponentOfZAxis
    axis_reference[1] = xComponentOfZAxis
    vtk.vtkMath.Normalize(axis_reference)
    # the result is in reference coordinates, move to source
    referenceToSourceTransform = vtk.vtkTransform()
    referenceToSourceTransform.DeepCopy(sourceToReferenceTransform)
    referenceToSourceTransform.Inverse()
    axis_source = referenceToSourceTransform.TransformVector(axis_reference)
    sourceToCorrectedTransform = vtk.vtkTransform()
    sourceToCorrectedTransform.RotateWXYZ(angle_source,axis_source)
    # now concatenate to the desired transforms
    correctedToSourceTransform = vtk.vtkTransform()
    correctedToSourceTransform.DeepCopy(sourceToCorrectedTransform)
    correctedToSourceTransform.Inverse()
    correctedToReferenceTransform = vtk.vtkTransform()
    correctedToReferenceTransform.PreMultiply()
    correctedToReferenceTransform.Concatenate(sourceToReferenceTransform)
    correctedToReferenceTransform.Concatenate(correctedToSourceTransform)

    xAxis = [1, 0, 0]
    correctedToReferenceXAxis = correctedToReferenceTransform.TransformVectorAtPoint(zeroVector, xAxis)
    if labelTransformSpinAroundZAxisXComponent and labelTransformSpinAroundZAxisXComponent in metricList:
      dotProductXOnRestingY = correctedToReferenceXAxis[1]
      if dotProductXOnRestingY > 1:
        dotProductXOnRestingY = 1
      if dotProductXOnRestingY < -1:
        dotProductXOnRestingY = -1
      transformSpinAroundZAxisXComponent = numpy.arcsin(-dotProductXOnRestingY) / numpy.pi * 180 #clockwise
      # arcsine only goes to 90 degrees. If the angle is greater,
      # then we need to account for that. The angle will only be greater
      # when the sign of element of x resting on x is less than 0.
      # because, in other words, cos(t) < 1 when t > 90 or t < -90
      dotProductXOnRestingX = correctedToReferenceXAxis[0]
      if dotProductXOnRestingX < 0:
        if transformSpinAroundZAxisXComponent < 0:
          transformSpinAroundZAxisXComponent = -180 - transformSpinAroundZAxisXComponent
        else:
          transformSpinAroundZAxisXComponent = 180 - transformSpinAroundZAxisXComponent
      arrayIndex = metricList.index(labelTransformSpinAroundZAxisXComponent)
      outputMetricsArray.SetTuple1(arrayIndex, transformSpinAroundZAxisXComponent)

    yAxis = [0, 1, 0]
    correctedToReferenceYAxis = correctedToReferenceTransform.TransformVectorAtPoint(zeroVector, yAxis)
    if labelTransformSpinAroundZAxisYComponent and labelTransformSpinAroundZAxisYComponent in metricList:
      dotProductYOnRestingX = correctedToReferenceYAxis[0]
      if dotProductYOnRestingX > 1:
        dotProductYOnRestingX = 1
      if dotProductYOnRestingX < -1:
        dotProductYOnRestingX = -1
      transformSpinAroundZAxisYComponent = numpy.arcsin(dotProductYOnRestingX) / numpy.pi * 180 #clockwise
      # arcsine only goes to 90 degrees. If the angle is greater,
      # then we need to account for that. The angle will only be greater
      # when the sign of element of y resting on y is less than 0.
      # because, in other words, cos(t) < 0 when t > 90 or t < -90
      dotProductYOnRestingY = correctedToReferenceYAxis[1]
      if dotProductYOnRestingY < 0:
        if transformSpinAroundZAxisYComponent < 0:
          transformSpinAroundZAxisYComponent = -180 - transformSpinAroundZAxisYComponent
        else:
          transformSpinAroundZAxisYComponent = 180 - transformSpinAroundZAxisYComponent
      arrayIndex = metricList.index(labelTransformSpinAroundZAxisYComponent)
      outputMetricsArray.SetTuple1(arrayIndex, transformSpinAroundZAxisYComponent)

    if labelTransformDifferenceOverallAngle and labelTransformDifferenceOverallAngle in metricList:
      axisAngleSourceToReference = sourceToReferenceTransform.GetOrientationWXYZ()
      transformDifferenceOverallAngleDeg = axisAngleSourceToReference[0]
      if transformDifferenceOverallAngleDeg > 180:
        transformDifferenceOverallAngleDeg = transformDifferenceOverallAngleDeg - 360
      # in this case there is no meaning in the sign of the computed value
      transformDifferenceOverallAngleDeg = numpy.abs(transformDifferenceOverallAngleDeg)
      arrayIndex = metricList.index(labelTransformDifferenceOverallAngle)
      outputMetricsArray.SetTuple1(arrayIndex, transformDifferenceOverallAngleDeg)

  def computeCauteryTipMetrics(self, cauteryTip, polyData, labelCauteryTipDistance, metricList, outputMetricsArray):
    if labelCauteryTipDistance and labelCauteryTipDistance in metricList:
      polyDataDistanceFilter = vtk.vtkImplicitPolyDataDistance()
      polyDataDistanceFilter.SetInput(polyData)
      arrayIndex = metricList.index(labelCauteryTipDistance)
      outputMetricsArray.SetTuple1(arrayIndex, polyDataDistanceFilter.EvaluateFunction(cauteryTip))

  def beginCaseMetricComputation(self):
    self.initializeMetrics()
    self.sequenceBrowserNode.SetSelectedItemNumber(0)
    self.caseMetricComputationTimer = qt.QTimer()
    self.caseMetricComputationTimer.setSingleShot(False)
    self.caseMetricComputationTimer.setInterval(10) # Once every 100th of a second
    self.caseMetricComputationTimer.connect('timeout()', self.caseMetricComputationTimeout)
    self.caseMetricComputationTimer.start()

  def caseMetricComputationTimeout(self):
    if self.caseMetricComputationTimer.isActive():
      self.caseMetricComputationTimer.stop()
    print( str(self.sequenceBrowserNode.GetSelectedItemNumber()) )
    self.computeMetrics()
    currentIndex = self.sequenceBrowserNode.SelectNextItem()
    if (currentIndex == 0):
      self.endCaseMetricComputation()
    else:
      self.caseMetricComputationTimer.start()

  def endCaseMetricComputation(self):
    self.caseMetricComputationTimer.disconnect('timeout()', self.caseMetricComputationTimeout)
    slicer.util.saveNode(self.metricsTable, self.tumorTrackingDirectory + 'computedMetrics.csv')
    self.currentCaseDone = True

  def beginAutomaticMetricComputation(self):
    self.caseFolders = \
      [
        "C:/D/data/BreastSurgeryCases/2016-01-19_NonPalpableCase03/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-01-19_NonPalpableCase04/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-01-21_NonPalpableCase05/TumorTrackingEval/",
        #"C:/D/data/BreastSurgeryCases/2016-02-01_NonPalpableCase06/TumorTrackingEval/", #non-synchronised
        "C:/D/data/BreastSurgeryCases/2016-02-01_NonPalpableCase07/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-02-09_NonPalpableCase08/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-02-16_NonPalpableCase09/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-03-22_NonPalpableCase10/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-03-29_NonPalpableCase11/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-03-29_NonPalpableCase12/TumorTrackingEval/",
        #"C:/D/data/BreastSurgeryCases/2016-05-02_NonPalpableCase13/TumorTrackingEval/", # could not find needle
        "C:/D/data/BreastSurgeryCases/2016-05-25_NonPalpableCase14/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-05-25_NonPalpableCase15/TumorTrackingEval/",
        #"C:/D/data/BreastSurgeryCases/2016-06-17_NonPalpableCase16/TumorTrackingEval/", # could not find needle
        # 17 omitted because data is incomplete
        "C:/D/data/BreastSurgeryCases/2016-07-07_NonpalpableCase18/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-08-30_NonpalpableCase19/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-09-13_NonpalpableCase20/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-09-19_NonpalpableCase21/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-09-20_NonpalpableCase22/TumorTrackingEval/",
        "C:/D/data/BreastSurgeryCases/2016-11-22_NonPalpableCase23/TumorTrackingEval/"
      ]
    self.currentCaseDone = True
    self.currentCase = -1
    self.automaticMetricComputationTimer = qt.QTimer()
    self.automaticMetricComputationTimer.setSingleShot(False)
    self.automaticMetricComputationTimer.setInterval(1000) # Once every second
    self.automaticMetricComputationTimer.connect('timeout()', self.automaticMetricComputationTimeout)
    self.automaticMetricComputationTimeout()

  def automaticMetricComputationTimeout(self):
    if self.automaticMetricComputationTimer.isActive():
      self.automaticMetricComputationTimer.stop()

    if not self.currentCaseDone:
      self.automaticMetricComputationTimer.start()
    else:
      self.currentCase = self.currentCase + 1
      if self.currentCase < len(self.caseFolders):
        self.loadAllData(self.caseFolders[self.currentCase])
        self.updateTumorModels()
        self.changeToTrackingData()
        self.setupTumorTracking()
        self.beginCaseMetricComputation()
        self.automaticMetricComputationTimer.start()
        self.currentCaseDone = False
      else:
        self.endAutomaticMetricComputation()

  def endAutomaticMetricComputation(self):
    self.automaticMetricComputationTimer.disconnect('timeout()', self.automaticMetricComputationTimeout)

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
    #slicer.app.coreIOManager().loadNodes('MarkupsFiducials',{'fileName':self.tumorTrackingDirectory+name+".fcsv"})
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

class TumorTrackingEvalTest(ScriptedLoadableModuleTest):
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
    self.test_TumorTrackingEval1()

  def test_TumorTrackingEval1(self):
    self.delayDisplay('No tests implemented yet!')
