## 说明

在本题中，你需要写一个`Makefile`文件，或者`CMakeLists.txt`文件，来编译handout中所提供的三个简单程序。

其中，`hello_cuda.cu`是一个简单的cuda程序，`hello_mpi.cpp`是一个简单的mpi程序，`hello_omp.cpp`是一个简单的openmp程序。它们都做了同一个事情：从文件中读取一个向量并求和。

你需要上传`Makefile`或者`CMakeLists.txt`文件。我们会根据以下策略来评测你所写的配置文件的正确性。

- 对于`Makefile`文件，我们会在项目根目录下执行`make`命令。然后在项目根目录下检查程序是否被生成，并运行以检测正确性。
- 对于`CMakeLists.txt`文件，我们会在项目根目录下执行`mkdir build; cd build; cmake ..; make`。然后我们会在build目录下检查程序是否被正确生成，并运行以检测正确性。
- 对于所有类型的文件，`hello_cuda.cu`所编译出的文件名应为`hello_cuda`；`hello_mpi.cpp`所编译出的文件名应为`hello_mpi`；`hello_omp.cpp`所编译出的文件名应为`hello_omp`。
