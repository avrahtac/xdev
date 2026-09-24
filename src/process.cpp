#include "xdev/process.hpp"
#include <cstdlib>
#include <array>
#include <cstdio>

#ifndef _WIN32
#include <sys/wait.h>
#endif

namespace xdev {

ProcessResult Process::run(const std::string& command) {
    ProcessResult result{ -1, "", "" };
    std::string cmd_with_err = command + " 2>&1";
    
    std::array<char, 128> buffer;
    
#ifdef _WIN32
    FILE* pipe = _popen(cmd_with_err.c_str(), "r");
#else
    FILE* pipe = popen(cmd_with_err.c_str(), "r");
#endif

    if (!pipe) {
        result.std_err = "popen() failed to start process.";
        return result;
    }
    
    while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
        result.std_out += buffer.data();
    }
    
    int raw_code = 0;
#ifdef _WIN32
    raw_code = _pclose(pipe);
    result.exit_code = raw_code;
#else
    raw_code = pclose(pipe);
    if (WIFEXITED(raw_code)) {
        result.exit_code = WEXITSTATUS(raw_code);
    } else {
        result.exit_code = raw_code;
    }
#endif
    
    return result;
}

int Process::run_interactive(const std::string& command) {
    int res = std::system(command.c_str());
#ifndef _WIN32
    if (WIFEXITED(res)) {
        return WEXITSTATUS(res);
    }
#endif
    return res;
}

} // namespace xdev