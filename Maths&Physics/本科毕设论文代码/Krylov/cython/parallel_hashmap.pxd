# distutils: language=c++

from libcpp.utility cimport pair


cdef extern from "<mutex>" namespace "std" nogil:
    cdef cppclass mutex:
        void lock() except +
        void unlock() except +


cdef extern from "../parallel_hashmap/phmap.h" namespace "phmap" nogil:
    cdef cppclass Hash[T]:
        pass
    cdef cppclass EqualTo[T]:
        pass
    cdef cppclass Allocator[T]:
        pass
    cdef cppclass four "4":
        pass
        # https://stackoverflow.com/questions/40323938/cython-c-templates


cdef extern from "../parallel_hashmap/phmap.h" namespace "phmap" nogil:
    cdef cppclass parallel_flat_hash_map[T, U, HASH=*, PRED=*, ALLOCATOR=*, N=*, MTX=*]:
        ctypedef T key_type
        ctypedef U mapped_type
        ctypedef pair[const T, U] value_type
        # ctypedef MTX mutex_type
        cppclass iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(iterator)
            bint operator!=(iterator)
        cppclass reverse_iterator:
            pair[T, U]& operator*()
            iterator operator++()
            iterator operator--()
            bint operator==(reverse_iterator)
            bint operator!=(reverse_iterator)
        cppclass const_iterator(iterator):
            pass
        cppclass const_reverse_iterator(reverse_iterator):
            pass
        parallel_flat_hash_map() except +
        parallel_flat_hash_map(parallel_flat_hash_map) except +
        #parallel_flat_hash_map(key_compare&)
        U& operator[](T&)
        #parallel_flat_hash_map& operator=(parallel_flat_hash_map&)
        bint operator==(parallel_flat_hash_map, parallel_flat_hash_map)
        bint operator!=(parallel_flat_hash_map, parallel_flat_hash_map)
        bint operator<(parallel_flat_hash_map, parallel_flat_hash_map)
        bint operator>(parallel_flat_hash_map, parallel_flat_hash_map)
        bint operator<=(parallel_flat_hash_map, parallel_flat_hash_map)
        bint operator>=(parallel_flat_hash_map, parallel_flat_hash_map)
        U& at(const T&)
        const U& const_at "at"(const T&)
        iterator begin()
        const_iterator const_begin "begin"()
        void clear()
        size_t count(T&)
        bint empty()
        iterator end()
        const_iterator const_end "end"()
        pair[iterator, iterator] equal_range(T&)
        pair[const_iterator, const_iterator] const_equal_range "equal_range"(const T&)
        iterator erase(iterator)
        iterator erase(iterator, iterator)
        size_t erase(T&)
        iterator find(T&)
        const_iterator const_find "find"(T&)
        pair[iterator, bint] insert(pair[T, U]) # XXX pair[T,U]&
        iterator insert(iterator, pair[T, U]) # XXX pair[T,U]&
        iterator insert(iterator, iterator)
        #key_compare key_comp()
        iterator lower_bound(T&)
        const_iterator const_lower_bound "lower_bound"(T&)
        size_t max_size()
        reverse_iterator rbegin()
        const_reverse_iterator const_rbegin "rbegin"()
        reverse_iterator rend()
        const_reverse_iterator const_rend "rend"()
        size_t size()
        void swap(parallel_flat_hash_map)
        iterator upper_bound(T&)
        const_iterator const_upper_bound "upper_bound"(T&)
        #value_compare value_comp()
        void max_load_factor(float)
        float max_load_factor()
        void rehash(size_t)
        void reserve(size_t)
        size_t bucket_count()
        size_t max_bucket_count()
        size_t bucket_size(size_t)
        size_t bucket(const T&)