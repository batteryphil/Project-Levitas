CXX = g++
CXXFLAGS = -O3 -msse4.2 -I./include -std=c++17
SRC = ./src/main.cpp
OBJ = $(SRC:.cpp=.o)
TARGET = levitas_engine

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJ)

clean:
	rm -f $(OBJ) $(TARGET)
