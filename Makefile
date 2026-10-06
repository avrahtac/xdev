CXX = clang++
CXXFLAGS = -std=c++20 -O3 -Iinclude -Wall
TARGET = xdev

# Automatically find all source files in src/
SRCS = $(wildcard src/*.cpp)
OBJS = $(SRCS:.cpp=.o)

ifeq ($(OS),Windows_NT)
    TARGET := $(TARGET).exe
    LDFLAGS = -lws2_32
else
    LDFLAGS =
endif

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $(OBJS) -o $(TARGET) $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(TARGET)

install: all
	mkdir -p ~/.local/bin
	cp $(TARGET) ~/.local/bin/xdev
	@echo "Installed xdev to ~/.local/bin/xdev"