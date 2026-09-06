package test;

import java.util.List;
import java.util.stream.Collectors;

public class GoodAccumulator {
    // Should NOT trigger - uses Stream.collect()
    public List<String> collectNames(List<Item> items) {
        return items.stream()
            .map(Item::getName)
            .collect(Collectors.toList());  // GOOD: immutable collection
    }

    // Should NOT trigger - uses reduce()
    public int calculateSum(List<Integer> numbers) {
        return numbers.stream()
            .reduce(0, Integer::sum);  // GOOD: functional reduction
    }
}

class Item {
    public String getName() { return ""; }
}
