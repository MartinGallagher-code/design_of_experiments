This repository is a design of experiments helper It takes an input file, as detailed below, and creates an executable script that can be used to run experiments an analyze them using basic DOE approaches, such as full-factorial, plackett-butman, etc.

The input file is as such:

{
    "factors" : [
        ["<factor>", "<levels (low, high, etc)>", "...", "..."]
    ],
    "static_settings" : [

    ],
    "settings" " {
        "block_count" : 1,
        "test_script" : <test file location>,
        "operation" : "full_factorial",
        "processed_directory" : "",
        "out_directory" : "
    }
}