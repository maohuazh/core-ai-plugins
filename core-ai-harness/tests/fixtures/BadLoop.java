package test;

import java.util.ArrayList;
import java.util.List;

public class BadLoop {
    // Should trigger: no-traditional-for-loop
    public void traditionalForLoop(List<String> items) {
        for (int i = 0; i < items.size(); i++) {
            System.out.println(items.get(i));
        }
    }
}
