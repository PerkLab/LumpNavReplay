import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# ViewCenterTesting
#

class ViewCenterTesting(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ViewCenterTesting"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Thomas Vaughan (Queen's University)"]
    self.parent.helpText = """ """
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """ """

#
# ViewCenterTestingWidget
#

class ViewCenterTestingWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = ViewCenterTestingLogic()

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.lumpNavDataComboBox = slicer.qMRMLNodeComboBox()
    self.lumpNavDataComboBox.nodeTypes = ["vtkMRMLSequenceBrowserNode"]
    self.lumpNavDataComboBox.selectNodeUponCreation = True
    self.lumpNavDataComboBox.addEnabled = False
    self.lumpNavDataComboBox.removeEnabled = False
    self.lumpNavDataComboBox.noneEnabled = True
    self.lumpNavDataComboBox.showHidden = False
    self.lumpNavDataComboBox.showChildNodeTypes = False
    self.lumpNavDataComboBox.setMRMLScene( slicer.mrmlScene )
    self.lumpNavDataComboBox.setToolTip( "Which sequences are the lumpnav data in" )
    parametersFormLayout.addRow("LumpNav Sequences: ", self.lumpNavDataComboBox)
    self.lumpNavDataComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.targetModelComboBox = slicer.qMRMLNodeComboBox()
    self.targetModelComboBox.nodeTypes = ["vtkMRMLModelNode"]
    self.targetModelComboBox.selectNodeUponCreation = True
    self.targetModelComboBox.addEnabled = False
    self.targetModelComboBox.removeEnabled = False
    self.targetModelComboBox.noneEnabled = True
    self.targetModelComboBox.showHidden = False
    self.targetModelComboBox.showChildNodeTypes = False
    self.targetModelComboBox.setMRMLScene( slicer.mrmlScene )
    self.targetModelComboBox.setToolTip( "What is the target of the view." )
    parametersFormLayout.addRow("Target Model: ", self.targetModelComboBox)
    self.targetModelComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.startIndexSpinBox = qt.QSpinBox()
    self.startIndexSpinBox.setMinimum(0)
    self.startIndexSpinBox.setMaximum(100000)
    parametersFormLayout.addRow("Start Index:", self.startIndexSpinBox)

    self.endIndexSpinBox = qt.QSpinBox()
    self.endIndexSpinBox.setMinimum(0)
    self.endIndexSpinBox.setMaximum(100000)
    parametersFormLayout.addRow("End Index:", self.endIndexSpinBox)

    self.goToStartButton = qt.QPushButton("Go to start")
    parametersFormLayout.addRow(self.goToStartButton)
    self.goToStartButton.connect('clicked()', self.onGoToStartButtonPressed)

    self.leftViewComboBox = slicer.qMRMLNodeComboBox()
    self.leftViewComboBox.nodeTypes = ["vtkMRMLViewNode"]
    self.leftViewComboBox.selectNodeUponCreation = True
    self.leftViewComboBox.addEnabled = False
    self.leftViewComboBox.removeEnabled = False
    self.leftViewComboBox.noneEnabled = True
    self.leftViewComboBox.showHidden = False
    self.leftViewComboBox.showChildNodeTypes = False
    self.leftViewComboBox.setMRMLScene( slicer.mrmlScene )
    self.leftViewComboBox.setToolTip( "Left view in Slicer." )
    parametersFormLayout.addRow("Left View: ", self.leftViewComboBox)
    self.leftViewComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.leftViewLayout = qt.QHBoxLayout()
    self.leftViewSaveLoadLabel = qt.QLabel("Save/Load: ")
    self.leftViewLayout.addWidget(self.leftViewSaveLoadLabel)
    self.leftTransformComboBox = slicer.qMRMLNodeComboBox()
    self.leftTransformComboBox.setMRMLScene(slicer.mrmlScene)
    self.leftTransformComboBox.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.leftTransformComboBox.selectNodeUponCreation = True
    self.leftTransformComboBox.addEnabled = True
    self.leftTransformComboBox.renameEnabled = True
    self.leftTransformComboBox.removeEnabled = False
    self.leftTransformComboBox.noneEnabled = True
    self.leftTransformComboBox.showHidden = False
    self.leftTransformComboBox.showChildNodeTypes = False
    self.leftTransformComboBox.setMRMLScene( slicer.mrmlScene )
    self.leftTransformComboBox.setToolTip( "Transform for left view." )
    self.leftViewLayout.addWidget(self.leftTransformComboBox)
    self.leftTransformComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)
    self.leftViewSaveButton = qt.QPushButton("Save to")
    self.leftViewLayout.addWidget(self.leftViewSaveButton)
    self.leftViewSaveButton.connect('clicked()', self.onLeftViewSaveButtonPressed)
    self.leftViewLoadButton = qt.QPushButton("Load from")
    self.leftViewLayout.addWidget(self.leftViewLoadButton)
    self.leftViewLoadButton.connect('clicked()', self.onLeftViewLoadButtonPressed)
    parametersFormLayout.addRow(self.leftViewLayout)

    self.rightViewComboBox = slicer.qMRMLNodeComboBox()
    self.rightViewComboBox.nodeTypes = ["vtkMRMLViewNode"]
    self.rightViewComboBox.selectNodeUponCreation = True
    self.rightViewComboBox.addEnabled = False
    self.rightViewComboBox.removeEnabled = False
    self.rightViewComboBox.noneEnabled = True
    self.rightViewComboBox.showHidden = False
    self.rightViewComboBox.showChildNodeTypes = False
    self.rightViewComboBox.setMRMLScene( slicer.mrmlScene )
    self.rightViewComboBox.setToolTip( "Right view in Slicer." )
    parametersFormLayout.addRow("Right View: ", self.rightViewComboBox)
    self.rightViewComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.rightViewLayout = qt.QHBoxLayout()
    self.rightViewSaveLoadLabel = qt.QLabel("Save/Load: ")
    self.rightViewLayout.addWidget(self.rightViewSaveLoadLabel)
    self.rightTransformComboBox = slicer.qMRMLNodeComboBox()
    self.rightTransformComboBox.setMRMLScene(slicer.mrmlScene)
    self.rightTransformComboBox.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.rightTransformComboBox.selectNodeUponCreation = True
    self.rightTransformComboBox.addEnabled = True
    self.rightTransformComboBox.renameEnabled = True
    self.rightTransformComboBox.removeEnabled = False
    self.rightTransformComboBox.noneEnabled = True
    self.rightTransformComboBox.showHidden = False
    self.rightTransformComboBox.showChildNodeTypes = False
    self.rightTransformComboBox.setMRMLScene( slicer.mrmlScene )
    self.rightTransformComboBox.setToolTip( "Transform for right view." )
    self.rightViewLayout.addWidget(self.rightTransformComboBox)
    self.rightTransformComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)
    self.rightViewSaveButton = qt.QPushButton("Save to")
    self.rightViewLayout.addWidget(self.rightViewSaveButton)
    self.rightViewSaveButton.connect('clicked()', self.onRightViewSaveButtonPressed)
    self.rightViewLoadButton = qt.QPushButton("Load from")
    self.rightViewLayout.addWidget(self.rightViewLoadButton)
    self.rightViewLoadButton.connect('clicked()', self.onRightViewLoadButtonPressed)
    parametersFormLayout.addRow(self.rightViewLayout)

    self.screenCoordinatesTableComboBox = slicer.qMRMLNodeComboBox()
    self.screenCoordinatesTableComboBox.nodeTypes = ["vtkMRMLTableNode"]
    self.screenCoordinatesTableComboBox.selectNodeUponCreation = True
    self.screenCoordinatesTableComboBox.addEnabled = True
    self.screenCoordinatesTableComboBox.renameEnabled = True
    self.screenCoordinatesTableComboBox.removeEnabled = False
    self.screenCoordinatesTableComboBox.noneEnabled = True
    self.screenCoordinatesTableComboBox.showHidden = False
    self.screenCoordinatesTableComboBox.showChildNodeTypes = False
    self.screenCoordinatesTableComboBox.setMRMLScene( slicer.mrmlScene )
    self.screenCoordinatesTableComboBox.setToolTip( "Where store screen coordinates of target model." )
    parametersFormLayout.addRow("Screen Coordinates Table: ", self.screenCoordinatesTableComboBox)
    self.screenCoordinatesTableComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.beginReplayButton = qt.QPushButton("Replay")
    parametersFormLayout.addRow(self.beginReplayButton)
    self.beginReplayButton.connect('clicked()', self.onBeginReplayButtonPressed)

    self.layout.addStretch(1)

    self.onNodeChanged()

  def cleanup(self):
    pass

  def onNodeChanged(self):
    # Update buttons
    leftViewAndTransformSelected = self.leftViewComboBox.currentNode() and self.leftTransformComboBox.currentNode()
    self.leftViewSaveButton.enabled = leftViewAndTransformSelected
    self.leftViewLoadButton.enabled = leftViewAndTransformSelected
    rightViewAndTransformSelected = self.rightViewComboBox.currentNode() and self.rightTransformComboBox.currentNode()
    self.rightViewSaveButton.enabled = rightViewAndTransformSelected
    self.rightViewLoadButton.enabled = rightViewAndTransformSelected
    self.goToStartButton.enabled = self.lumpNavDataComboBox.currentNode()
    self.beginReplayButton.enabled = self.lumpNavDataComboBox.currentNode() and \
                                     self.targetModelComboBox.currentNode() and \
                                     self.screenCoordinatesTableComboBox.currentNode() and \
                                     self.leftViewComboBox.currentNode() and \
                                     self.rightViewComboBox.currentNode()

  def onLeftViewLoadButtonPressed(self):
    transformNode = self.leftTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    viewNode = self.leftViewComboBox.currentNode()
    if not viewNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    modelNode = self.targetModelComboBox.currentNode()
    self.logic.assignTransformDataToCameraNode( transformNode, viewNode, modelNode )

  def onRightViewLoadButtonPressed(self):
    transformNode = self.rightTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    viewNode = self.rightViewComboBox.currentNode()
    if not viewNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    modelNode = self.targetModelComboBox.currentNode()
    self.logic.assignTransformDataToCameraNode( transformNode, viewNode, modelNode )

  def onLeftViewSaveButtonPressed(self):
    viewNode = self.leftViewComboBox.currentNode()
    if not viewNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    transformNode = self.leftTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    self.logic.assignCameraDataToTransformNode( viewNode, transformNode )

  def onRightViewSaveButtonPressed(self):
    viewNode = self.rightViewComboBox.currentNode()
    if not viewNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    transformNode = self.rightTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    self.logic.assignCameraDataToTransformNode( viewNode, transformNode )

  def onGoToStartButtonPressed(self):
    sequenceBrowserNode = self.lumpNavDataComboBox.currentNode()
    startFrameIndex = self.startIndexSpinBox.value
    self.logic.goToStart(sequenceBrowserNode,startFrameIndex)

  def onBeginReplayButtonPressed(self):
    sequenceBrowserNode = self.lumpNavDataComboBox.currentNode()
    endFrameIndex = self.endIndexSpinBox.value
    tumorModelNode = self.targetModelComboBox.currentNode()
    leftViewNode = self.leftViewComboBox.currentNode()
    rightViewNode = self.rightViewComboBox.currentNode()
    tableNode = self.screenCoordinatesTableComboBox.currentNode()
    self.logic.beginReplay(sequenceBrowserNode,endFrameIndex,tumorModelNode,leftViewNode,rightViewNode,tableNode)

#
# ViewCenterTestingLogic
#

class ViewCenterTestingLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def assignTransformDataToCameraNode(self, viewToRasTransformNode, viewNode, modelNode):
    camerasLogic = slicer.modules.cameras.logic()
    cameraNode = camerasLogic.GetViewActiveCameraNode(viewNode)
    viewToRasTransform = vtk.vtkGeneralTransform()
    viewToRasTransform = viewToRasTransformNode.GetTransformToParent()
    originView = [ 0, 0, 0 ]
    originRas = viewToRasTransform.TransformPoint( originView )
    cameraNode.SetPosition( originRas )
    upDirectionView = [ 0, 1, 0 ]
    upDirectionRas = [ 0, 0, 0 ]
    viewToRasTransform.TransformVectorAtPoint( originView, upDirectionView, upDirectionRas )
    cameraNode.SetViewUp( upDirectionRas )
    focalPointView = [ 0, 0, -100 ] # default, but changes if modelNode is provided
    if modelNode:
      modelParentNode = modelNode.GetParentTransformNode()
      modelToViewTransform = vtk.vtkGeneralTransform()
      slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(modelParentNode, viewToRasTransformNode, modelToViewTransform)
      modelBounds = [0,0,0,0,0,0]
      modelNode.GetBounds(modelBounds)
      modelCenterX = (modelBounds[0] + modelBounds[1]) / 2
      modelCenterY = (modelBounds[2] + modelBounds[3]) / 2
      modelCenterZ = (modelBounds[4] + modelBounds[5]) / 2
      modelPosition = [modelCenterX, modelCenterY, modelCenterZ]
      modelPositionView = modelToViewTransform.TransformPoint( modelPosition )
      focalPointView = [ 0, 0, modelPositionView[2] ]
    focalPointRas = viewToRasTransform.TransformPoint( focalPointView )
    cameraNode.SetFocalPoint( focalPointRas )
    self.resetCameraClippingRange( viewNode )

  def assignCameraDataToTransformNode(self, viewNode, viewToRasTransformNode):
    camerasLogic = slicer.modules.cameras.logic()
    cameraNode = camerasLogic.GetViewActiveCameraNode(viewNode)
    viewToRasMatrix = vtk.vtkMatrix4x4()
    originRas = [ 0, 0, 0 ]
    cameraNode.GetPosition( originRas )
    viewToRasMatrix.SetElement( 0, 3, originRas[0] )
    viewToRasMatrix.SetElement( 1, 3, originRas[1] )
    viewToRasMatrix.SetElement( 2, 3, originRas[2] )
    focalPointRas = [ 0, 0, 0 ]
    cameraNode.GetFocalPoint( focalPointRas )
    screenDirectionRas = [ 0, 0, 0 ]
    vtk.vtkMath.Subtract( originRas, focalPointRas, screenDirectionRas )
    vtk.vtkMath.Normalize( screenDirectionRas )
    viewToRasMatrix.SetElement( 0, 2, screenDirectionRas[0] )
    viewToRasMatrix.SetElement( 1, 2, screenDirectionRas[1] )
    viewToRasMatrix.SetElement( 2, 2, screenDirectionRas[2] )
    upDirectionRas = [ 0, 0, 0 ]
    cameraNode.GetViewUp( upDirectionRas )
    viewToRasMatrix.SetElement( 0, 1, upDirectionRas[0] )
    viewToRasMatrix.SetElement( 1, 1, upDirectionRas[1] )
    viewToRasMatrix.SetElement( 2, 1, upDirectionRas[2] )
    rightDirectionRas = [ 0, 0, 0 ] # temporary values
    vtk.vtkMath.Cross( upDirectionRas, screenDirectionRas, rightDirectionRas )
    viewToRasMatrix.SetElement( 0, 0, rightDirectionRas[0] )
    viewToRasMatrix.SetElement( 1, 0, rightDirectionRas[1] )
    viewToRasMatrix.SetElement( 2, 0, rightDirectionRas[2] )
    viewToRasTransformNode.SetMatrixTransformToParent( viewToRasMatrix )

  def goToStart(self,sequenceBrowserNode,startFrameIndex):
    sequenceBrowserNode.SetSelectedItemNumber(startFrameIndex)

  def beginReplay(self,sequenceBrowserNode,endFrameIndex,tumorModelNode,leftViewNode,rightViewNode,tableNode):
    self.endFrameIndex = endFrameIndex
    self.sequenceBrowserNode = sequenceBrowserNode
    self.sequenceBrowserNode.SetPlaybackRateFps(9.5)
    self.sequenceBrowserNode.SetPlaybackActive(True)
    self.leftViewNode = leftViewNode
    self.rightViewNode = rightViewNode
    self.tumorModelNode = tumorModelNode
    self.tableNode = tableNode
    self.tableColumnIndices = vtk.vtkIntArray()
    self.tableColumnIndices.SetName("Index")
    self.tableColumnTime = vtk.vtkDoubleArray()
    self.tableColumnTime.SetName("Time (s)")
    self.tableColumnLeftMinimumX = vtk.vtkDoubleArray()
    self.tableColumnLeftMinimumX.SetName("Left View Minimum X Extent")
    self.tableColumnLeftMaximumX = vtk.vtkDoubleArray()
    self.tableColumnLeftMaximumX.SetName("Left View Maximum X Extent")
    self.tableColumnLeftMinimumY = vtk.vtkDoubleArray()
    self.tableColumnLeftMinimumY.SetName("Left View Minimum Y Extent")
    self.tableColumnLeftMaximumY = vtk.vtkDoubleArray()
    self.tableColumnLeftMaximumY.SetName("Left View Maximum Y Extent")
    self.tableColumnRightMinimumX = vtk.vtkDoubleArray()
    self.tableColumnRightMinimumX.SetName("Right View Minimum X Extent")
    self.tableColumnRightMaximumX = vtk.vtkDoubleArray()
    self.tableColumnRightMaximumX.SetName("Right View Maximum X Extent")
    self.tableColumnRightMinimumY = vtk.vtkDoubleArray()
    self.tableColumnRightMinimumY.SetName("Right View Minimum Y Extent")
    self.tableColumnRightMaximumY = vtk.vtkDoubleArray()
    self.tableColumnRightMaximumY.SetName("Right View Maximum Y Extent")
    self.timer = qt.QTimer()
    self.timer.setSingleShot(False)
    self.timer.setInterval(100) # Once every 10th of a second
    self.timer.connect('timeout()', self.onTimeout)
    self.timer.start()

  def onTimeout(self):
    if self.timer.isActive():
      self.timer.stop()
    currentIndex = self.sequenceBrowserNode.GetSelectedItemNumber()
    self.tableColumnIndices.InsertNextTuple1(currentIndex)
    timeSeconds = float(self.sequenceBrowserNode.GetMasterSequenceNode().GetNthIndexValue(currentIndex))
    self.tableColumnTime.InsertNextTuple1(timeSeconds)
    leftViewExtents = self.computeExtentsOfModelInViewport(self.leftViewNode,self.tumorModelNode)
    self.tableColumnLeftMinimumX.InsertNextTuple1(leftViewExtents[0])
    self.tableColumnLeftMaximumX.InsertNextTuple1(leftViewExtents[1])
    self.tableColumnLeftMinimumY.InsertNextTuple1(leftViewExtents[2])
    self.tableColumnLeftMaximumY.InsertNextTuple1(leftViewExtents[3])
    rightViewExtents = self.computeExtentsOfModelInViewport(self.rightViewNode,self.tumorModelNode)
    self.tableColumnRightMinimumX.InsertNextTuple1(rightViewExtents[0])
    self.tableColumnRightMaximumX.InsertNextTuple1(rightViewExtents[1])
    self.tableColumnRightMinimumY.InsertNextTuple1(rightViewExtents[2])
    self.tableColumnRightMaximumY.InsertNextTuple1(rightViewExtents[3])
    if (currentIndex >= self.endFrameIndex):
      self.sequenceBrowserNode.SetPlaybackActive(False)
      self.endReplay()
    else:
      self.timer.start()

  def endReplay(self):
    self.tableNode.RemoveAllColumns()
    self.tableNode.AddColumn(self.tableColumnIndices)
    self.tableNode.AddColumn(self.tableColumnTime)
    self.tableNode.AddColumn(self.tableColumnLeftMinimumX)
    self.tableNode.AddColumn(self.tableColumnLeftMaximumX)
    self.tableNode.AddColumn(self.tableColumnLeftMinimumY)
    self.tableNode.AddColumn(self.tableColumnLeftMaximumY)
    self.tableNode.AddColumn(self.tableColumnRightMinimumX)
    self.tableNode.AddColumn(self.tableColumnRightMaximumX)
    self.tableNode.AddColumn(self.tableColumnRightMinimumY)
    self.tableNode.AddColumn(self.tableColumnRightMaximumY)

  def computeExtentsOfModelInViewport(self, viewNode, modelNode):
    modelToRasTransform = vtk.vtkGeneralTransform()
    modelToRasTransformNode = modelNode.GetParentTransformNode()
    modelToRasTransformNode.GetTransformToWorld(modelToRasTransform)
    transformFilter = vtk.vtkTransformFilter()
    transformFilter.SetTransform(modelToRasTransform)
    transformFilter.SetInputData(modelNode.GetPolyData())
    transformFilter.Update()
    pointsRas = transformFilter.GetOutput().GetPoints()
    numberOfPoints = pointsRas.GetNumberOfPoints()
    minimumXViewport = float('inf')
    maximumXViewport = float('-inf')
    minimumYViewport = float('inf')
    maximumYViewport = float('-inf')
    minimumZViewport = float('inf')
    maximumZViewport = float('-inf')
    for pointIndex in xrange(0, numberOfPoints):
      pointRas = [0,0,0]
      pointsRas.GetPoint(pointIndex,pointRas)
      pointViewport = self.convertRasToViewport(viewNode,pointRas)
      xViewport = pointViewport[0]
      if xViewport < minimumXViewport:
        minimumXViewport = xViewport
      if xViewport > maximumXViewport:
        maximumXViewport = xViewport
      yViewport = pointViewport[1]
      if yViewport < minimumYViewport:
        minimumYViewport = yViewport
      if yViewport > maximumYViewport:
        maximumYViewport = yViewport
      zViewport = pointViewport[2]
      if zViewport < minimumZViewport:
        minimumZViewport = zViewport
      if zViewport > maximumZViewport:
        maximumZViewport = zViewport
    extentsViewport = [minimumXViewport,maximumXViewport,minimumYViewport,maximumYViewport,minimumZViewport,maximumZViewport]
    return extentsViewport

  def convertRasToViewport(self, viewNode, positionRas):
    """Computes normalized view coordinates from RAS coordinates for a particular view
    Normalized view coordinates origin is in bottom-left corner, range is [-1,+1]
    """
    x = vtk.mutable(positionRas[0])
    y = vtk.mutable(positionRas[1])
    z = vtk.mutable(positionRas[2])
    view = slicer.app.layoutManager().threeDWidget(self.getThreeDWidgetIndex(viewNode)).threeDView()
    renderer = view.renderWindow().GetRenderers().GetItemAsObject(0)
    renderer.WorldToView(x,y,z)
    return [x.get(), y.get(), z.get()]

  def getThreeDWidgetIndex(self, viewNode):
    if (not viewNode):
      logging.error("Error in getThreeDWidgetIndex: No View node selected. Returning 0.")
      return 0
    layoutManager = slicer.app.layoutManager()
    for threeDViewIndex in xrange(layoutManager.threeDViewCount):
      threeDViewNode = layoutManager.threeDWidget(threeDViewIndex).threeDView().mrmlViewNode()
      if (threeDViewNode == viewNode):
        return threeDViewIndex
    logging.error("Error in getThreeDWidgetIndex: Can't find the index. Selected View does not exist? Returning 0.")
    return 0

  def resetCameraClippingRange(self, viewNode):
    view = slicer.app.layoutManager().threeDWidget(self.getThreeDWidgetIndex(viewNode)).threeDView()
    renderer = view.renderWindow().GetRenderers().GetItemAsObject(0)
    renderer.ResetCameraClippingRange()


class ViewCenterTestingTest(ScriptedLoadableModuleTest):
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
    self.test_ViewCenterTesting1()

  def test_ViewCenterTesting1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = ViewCenterTestingLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
