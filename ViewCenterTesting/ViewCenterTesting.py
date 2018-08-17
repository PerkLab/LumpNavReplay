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

    self.screenCoordinatesTableComboBox = slicer.qMRMLNodeComboBox()
    self.screenCoordinatesTableComboBox.nodeTypes = ["vtkMRMLTableNode"]
    self.screenCoordinatesTableComboBox.selectNodeUponCreation = True
    self.screenCoordinatesTableComboBox.addEnabled = True
    self.screenCoordinatesTableComboBox.removeEnabled = False
    self.screenCoordinatesTableComboBox.noneEnabled = True
    self.screenCoordinatesTableComboBox.showHidden = False
    self.screenCoordinatesTableComboBox.showChildNodeTypes = False
    self.screenCoordinatesTableComboBox.setMRMLScene( slicer.mrmlScene )
    self.screenCoordinatesTableComboBox.setToolTip( "Where store screen coordinates of target model." )
    parametersFormLayout.addRow("Screen Coordinates Table: ", self.screenCoordinatesTableComboBox)
    self.screenCoordinatesTableComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.leftCameraComboBox = slicer.qMRMLNodeComboBox()
    self.leftCameraComboBox.nodeTypes = ["vtkMRMLCameraNode"]
    self.leftCameraComboBox.selectNodeUponCreation = True
    self.leftCameraComboBox.addEnabled = False
    self.leftCameraComboBox.removeEnabled = False
    self.leftCameraComboBox.noneEnabled = True
    self.leftCameraComboBox.showHidden = False
    self.leftCameraComboBox.showChildNodeTypes = False
    self.leftCameraComboBox.setMRMLScene( slicer.mrmlScene )
    self.leftCameraComboBox.setToolTip( "Left view in Slicer." )
    parametersFormLayout.addRow("Left View: ", self.leftCameraComboBox)
    self.leftCameraComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.leftViewLayout = qt.QHBoxLayout()
    self.leftViewSaveLoadLabel = qt.QLabel("Left View Loading/Saving: ")
    self.leftViewLayout.addWidget(self.leftViewSaveLoadLabel)
    self.leftTransformComboBox = slicer.qMRMLNodeComboBox()
    self.leftTransformComboBox.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.leftTransformComboBox.selectNodeUponCreation = True
    self.leftTransformComboBox.addEnabled = True
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

    self.rightCameraComboBox = slicer.qMRMLNodeComboBox()
    self.rightCameraComboBox.nodeTypes = ["vtkMRMLCameraNode"]
    self.rightCameraComboBox.selectNodeUponCreation = True
    self.rightCameraComboBox.addEnabled = False
    self.rightCameraComboBox.removeEnabled = False
    self.rightCameraComboBox.noneEnabled = True
    self.rightCameraComboBox.showHidden = False
    self.rightCameraComboBox.showChildNodeTypes = False
    self.rightCameraComboBox.setMRMLScene( slicer.mrmlScene )
    self.rightCameraComboBox.setToolTip( "Right view in Slicer." )
    parametersFormLayout.addRow("Right View: ", self.rightCameraComboBox)
    self.rightCameraComboBox.connect("currentNodeChanged(vtkMRMLNode*)", self.onNodeChanged)

    self.rightViewLayout = qt.QHBoxLayout()
    self.rightViewSaveLoadLabel = qt.QLabel("Right View Loading/Saving: ")
    self.rightViewLayout.addWidget(self.rightViewSaveLoadLabel)
    self.rightTransformComboBox = slicer.qMRMLNodeComboBox()
    self.rightTransformComboBox.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.rightTransformComboBox.selectNodeUponCreation = True
    self.rightTransformComboBox.addEnabled = True
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

    self.startIndexSpinBox = qt.QSpinBox()
    parametersFormLayout.addRow("Start Index:", self.startIndexSpinBox)

    self.endIndexSpinBox = qt.QSpinBox()
    parametersFormLayout.addRow("End Index:", self.endIndexSpinBox)

    self.goToStartButton = qt.QPushButton("Go to start")
    parametersFormLayout.addRow(self.goToStartButton)
    self.goToStartButton.connect('clicked()', self.onGoToStartButtonPressed)

    self.beginReplayButton = qt.QPushButton("Replay")
    parametersFormLayout.addRow(self.beginReplayButton)
    self.beginReplayButton.connect('clicked()', self.onBeginReplayButtonPressed)

    self.layout.addStretch(1)

    self.onNodeChanged()

  def cleanup(self):
    pass

  def onNodeChanged(self):
    # Update buttons
    leftViewAndTransformSelected = self.leftCameraComboBox.currentNode() and self.leftTransformComboBox.currentNode()
    self.leftViewSaveButton.enabled = leftViewAndTransformSelected
    self.leftViewLoadButton.enabled = leftViewAndTransformSelected
    rightViewAndTransformSelected = self.rightCameraComboBox.currentNode() and self.rightTransformComboBox.currentNode()
    self.rightViewSaveButton.enabled = rightViewAndTransformSelected
    self.rightViewLoadButton.enabled = rightViewAndTransformSelected
    self.goToStartButton.enabled = self.lumpNavDataComboBox.currentNode()
    self.beginReplayButton.enabled = self.lumpNavDataComboBox.currentNode() and \
                                     self.targetModelComboBox.currentNode() and \
                                     self.screenCoordinatesTableComboBox.currentNode() and \
                                     self.leftCameraComboBox.currentNode() and \
                                     self.rightCameraComboBox.currentNode()

  def onLeftViewLoadButtonPressed(self):
    logic = ViewCenterTestingLogic()
    transformNode = self.leftTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    cameraNode = self.leftCameraComboBox.currentNode()
    if not cameraNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    modelNode = self.targetModelComboBox.currentNode()
    logic.assignTransformDataToCameraNode( transformNode, cameraNode, modelNode )

  def onRightViewLoadButtonPressed(self):
    logic = ViewCenterTestingLogic()
    transformNode = self.rightTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    cameraNode = self.rightCameraComboBox.currentNode()
    if not cameraNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    modelNode = self.targetModelComboBox.currentNode()
    logic.assignTransformDataToCameraNode( transformNode, cameraNode, modelNode )

  def onLeftViewSaveButtonPressed(self):
    logic = ViewCenterTestingLogic()
    cameraNode = self.leftCameraComboBox.currentNode()
    if not cameraNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    transformNode = self.leftTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    logic.assignCameraDataToTransformNode( cameraNode, transformNode )

  def onRightViewSaveButtonPressed(self):
    logic = ViewCenterTestingLogic()
    cameraNode = self.rightCameraComboBox.currentNode()
    if not cameraNode:
      logging.error( "Cannot save or load view when camera node is null." )
      return
    transformNode = self.rightTransformComboBox.currentNode()
    if not transformNode:
      logging.error( "Cannot save or load view when transform node is null." )
      return
    logic.assignCameraDataToTransformNode( cameraNode, transformNode )

  def onGoToStartButtonPressed(self):
    pass

  def onBeginReplayButtonPressed(self):
    pass

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

  def assignTransformDataToCameraNode(self, viewToRasTransformNode, cameraNode, modelNode):
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
    cameraNode.ResetClippingRange()

  def assignCameraDataToTransformNode(self, cameraNode, viewToRasTransformNode):
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
