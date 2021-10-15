CONFIG -= qt

TEMPLATE = lib
CONFIG += c++11 no_keywords

SOURCES += \
    boopy.cpp \

win32 {
    INCLUDEPATH += ../../../Addons/boost_1_75_0 ../../../../../anaconda3/Library/include
    INCLUDEPATH += ../../../../../anaconda3/include
    LIBS += -L../../../../../anaconda3/libs
    TARGET_EXT=.pyd
}
unix:INCLUDEPATH += ../Beamfox/Addons/boost_1_60_0
