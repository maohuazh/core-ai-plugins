package test;

public class GoodMutation {
    // Should NOT trigger any rules - uses new variable
    public void noMutation(String name) {
        String upperName = name.toUpperCase();  // GOOD: new variable
        System.out.println(upperName);
    }

    // Should NOT trigger - uses return value
    public int increment(int value) {
        return value + 1;  // GOOD: returns new value, doesn't mutate
    }
}
