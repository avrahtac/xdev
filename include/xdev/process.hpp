#pragma once
#include <string>

namespace xdev {
struct ProcessResult {
    int exit_code;
    std::string std_out;
    std::string std_err;
};

class Process {
public:
    // Captures output internally (useful for `doctor` dependency checks)
    static ProcessResult run(const std::string& command);
    
    // Connects directly to the terminal (useful for `build` and `run` where we want to see live output)
    static int run_interactive(const std::string& command);
};
}