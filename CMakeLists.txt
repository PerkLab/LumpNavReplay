cmake_minimum_required(VERSION 3.5)

project(LumpNavReplay)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/ViewCenterTesting")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Thomas Vaughan (Queen's University), Shaun Lund (Queen's University)")
set(EXTENSION_DESCRIPTION "Modules for replaying navigated lumpectomy data")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/ViewCenterTesting.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/ViewCenterTesting/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(LumpNavReplay)
add_subdirectory(ViewCenterTesting)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
