#pragma once
#include <string>

namespace xdev {
class Platform {
public:
    static std::string get_os();
    static std::string get_architecture();
};
}