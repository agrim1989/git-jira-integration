import threading
import time

# Define a function to simulate a long-running task
def long_running_task(thread_name):
    """Simulate a long-running task"""
    print(f"{thread_name} started")
    for i in range(10):
        print(f"{thread_name}: {i}")
        time.sleep(1)  # Simulate some work
    print(f"{thread_name} finished")

# Define a function to explain GIL in depth
def explain_gil():
    """Explain the Global Interpreter Lock (GIL) in depth"""
    print("Global Interpreter Lock (GIL) Explanation:")
    print("-----------------------------------------")
    print("The GIL is a mechanism used in Python to synchronize access to Python objects")
    print("It prevents multiple native threads from executing Python bytecodes at once")
    print("This lock is necessary because Python's memory management is not thread-safe")

def main():
    explain_gil()

    # Create two threads to run the long-running task
    thread1 = threading.Thread(target=long_running_task, args=("Thread-1",))
    thread2 = threading.Thread(target=long_running_task, args=("Thread-2",))

    # Start the threads
    thread1.start()
    thread2.start()

    # Wait for the threads to finish
    thread1.join()
    thread2.join()

if __name__ == "__main__":
    main()