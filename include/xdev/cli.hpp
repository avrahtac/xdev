#pragma once

namespace xdev {
class CLI {
public:
    static int run(int argc, char* argv[]);
private:
    static void print_help();
    static void print_version();
};
}
