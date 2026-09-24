#pragma once
#include <string>

namespace xdev {

class Fetch {
public:
    static int execute();

private:
    static bool download_file(const std::string& url, const std::string& destination);
};

} // namespace xdev