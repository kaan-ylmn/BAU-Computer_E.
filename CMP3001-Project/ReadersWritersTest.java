import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;


class ReadWriteLock {
    private Semaphore mutex = new Semaphore(1);
    private Semaphore write = new Semaphore(1);
    private int r_cont = 0;

    public void readLock() {
        try {
            mutex.acquire();
            r_cont++;
            if (r_cont == 1) {
                write.acquire();
            }
            mutex.release();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void writeLock() {
        try {
            write.acquire();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void readUnLock() {
        try {
            mutex.acquire();
            r_cont--;
            if (r_cont == 0) {
                write.release();
            }
            mutex.release();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void writeUnLock() {
        write.release();
    }
}


public class ReadersWritersTest {
    public static void main(String[] args) {
        ReadWriteLock lock = new ReadWriteLock();
        ExecutorService executor = Executors.newFixedThreadPool(10);

        for (int i = 0; i < 5; i++) {
            executor.execute(() -> {
                lock.readLock();
                System.out.println(Thread.currentThread().getName() + " is reading.");
                System.out.println(Thread.currentThread().getName() + " has finished reading.");
                lock.readUnLock();
            });
        }
        for (int i = 0; i < 2; i++) {
            executor.execute(() -> {
                lock.writeLock();
                System.out.println(Thread.currentThread().getName() + " is writing.");
                System.out.println(Thread.currentThread().getName() + " has finished writing.");
                lock.writeUnLock();
            });
        }
        executor.shutdown();
    }
}
