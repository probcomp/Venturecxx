#ifndef FILE_UTILS_H 
#define FILE_UTILS_H 

#include <vector>
#include <string>


bool str_ends_with(const std::string str, const std::string target_suffix);
std::vector<std::string> lsdir(std::string path_str);
std::vector<std::string> filter_for_suffix(const std::vector<std::string> in_vec, std::string suffix);
void print_string_v(const std::vector<std::string> string_v);
void remove_trailing_n_chars(std::vector<std::string> &in_vec, int n_chars);

#endif
