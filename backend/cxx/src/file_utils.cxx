#include <boost/filesystem.hpp>
#include <iostream>
#include <string>
#include <vector>


bool str_ends_with(const std::string str, const std::string target_suffix) {
	int target_suffix_len = target_suffix.length();
	int str_len = str.length();
	std::string str_suffix = str.substr(str_len - target_suffix_len, target_suffix_len);
	return str_suffix == target_suffix;
}

std::vector<std::string> lsdir(std::string path_str) {
	std::vector<std::string> ret_vec;
	boost::filesystem::path path(path_str);

	if (!boost::filesystem::exists(path)) {
		return ret_vec;
	}

	// default construction yields past-the-end
	boost::filesystem::directory_iterator end_itr; 
	for (boost::filesystem::directory_iterator itr(path);
			itr != end_itr;
			++itr )
	{
		if(boost::filesystem::is_directory(itr->status())) {
		} else {
			std::string str_copy = itr->path().leaf().string();
			ret_vec.push_back(str_copy);
		}
	}
	return ret_vec;
}

void remove_trailing_n_chars(std::vector<std::string> &in_vec, int n_chars) {
	for(std::vector<std::string>::iterator it=in_vec.begin(); it!=in_vec.end(); it++) {
		int new_str_len = (*it).length() - n_chars;
		(*it).resize(new_str_len);
	}
}

std::vector<std::string> filter_for_suffix(const std::vector<std::string> in_vec, std::string suffix) {
	std::vector<std::string> out_vec;
	for(std::vector<std::string>::const_iterator it=in_vec.begin(); it!=in_vec.end(); it++) {
		if(str_ends_with(*it, suffix)) {
			out_vec.push_back(*it);
		}
	}
	remove_trailing_n_chars(out_vec, suffix.length());
	return out_vec;
}

void print_string_v(const std::vector<std::string> string_v) {
	std::vector<std::string>::const_iterator it=string_v.begin();
	if(it==string_v.end()) return;
	std::cout << "[ " << *it++;
	for(; it!=string_v.end(); it++) {
		std::cout << ", " << *it;
	}
	std::cout << " ]" << std::endl;
}
