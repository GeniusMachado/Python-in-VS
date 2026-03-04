import sys 
import gc 

gc.disable() # Disable automatic garbage collection to see the effect of reference counting

class garbage_collector:
    def __init__(self):
        self.data = [i for i in range(1000000)]
    def __del__(self):
        print("Instance is being destroyed (sys.getrefcount() reached zero).")
        del self.data

if __name__ == "__main__":
    obj1 = garbage_collector()
    # Initial reference count will be higher than expected because sys.getrefcount() 
    # itself temporarily increases the count by one.
    print("Reference count of obj1:", sys.getrefcount(obj1)) 

    obj2 = obj1 # obj2 becomes another reference to the same object
    print("Reference count of obj1 after creating obj2:", sys.getrefcount(obj1)) 

    del obj2 # Removes one reference
    print("Reference count of obj1 after deleting obj2:", sys.getrefcount(obj1)) 

    del obj1 # Removes the final reference, triggering the __del__ method
    # At this point, the object is destroyed, and the next print statement will raise a NameError
    # because obj1 no longer exists.
    try:
        print("Reference count of obj1 after deleting obj1:", sys.getrefcount(obj1))
    except NameError as e:
        print("obj1 is no longer defined because it was deleted and the object destroyed.")

    gc.collect() # Force garbage collection - this call has no effect here because
                 # the object was already destroyed by reference counting.
