package test;

import java.util.ArrayList;
import java.util.List;

public class BadAccumulator {
    // Should trigger: no-mutable-accumulator
    public List<String> collectNames(List<Item> items) {
        List<String> names = new ArrayList<>();
        for (Item item : items) {
            names.add(item.getName());  // BAD: mutable accumulator (.add pattern)
        }
        return names;
    }

    // Should trigger: no-mutable-accumulator (enhanced for loop)
    public List<Integer> doubleValues(List<Integer> numbers) {
        List<Integer> result = new ArrayList<>();
        for (Integer n : numbers) {
            result.add(n * 2);  // BAD: mutable accumulator
        }
        return result;
    }
}

class Item {
    public String getName() { return ""; }
}
