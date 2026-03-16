cmake_minimum_required(VERSION 3.20)
project(Beziers3d)

set(CMAKE_CXX_STANDARD 20)

find_package(OpenGL REQUIRED)
find_package(GLUT REQUIRED)

add_executable(app src/main.cpp)

target_include_directories(app PRIVATE ${GLUT_INCLUDE_DIRS})
target_link_libraries(app PRIVATE ${OPENGL_LIBRARIES} ${GLUT_LIBRARIES})
