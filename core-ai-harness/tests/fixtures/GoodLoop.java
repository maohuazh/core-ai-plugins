package test;

import java.util.List;
import java.util.stream.Collectors;

public class GoodLoop {
    // Should NOT trigger any rules - uses Stream API
    public void streamLoop(List<String> items) {
        items.stream()
            .forEach(System.out::println);
    }

    public List<String> transformItems(List<String> items) {
        return items.stream()
            .map(String::toUpperCase)
            .collect(Collectors.toList());
    }
}
