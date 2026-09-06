package test;

public class BadMutation {
    // Should trigger: no-parameter-mutation
    public void mutateParameter(String name) {
        name = name.toUpperCase();  // BAD: mutating parameter
        System.out.println(name);
    }

    // Should trigger: no-parameter-mutation
    public void reassignParameter(int value) {
        value = value + 1;  // BAD: reassigning parameter
        System.out.println(value);
    }
}
