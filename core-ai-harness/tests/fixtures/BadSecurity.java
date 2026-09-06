package test;

import java.sql.*;

public class BadSecurity {
    public void bad() {
        String password = "hunter2secret";
        String apiKey = "sk-1234567890abcdef";
    }

    public void sql(Connection conn, String userId) {
        String query = "SELECT * FROM users WHERE id = '" + userId + "'";
    }

    public void swallow() {
        try {
            risky();
        } catch (Exception e) {
        }
    }
    void risky() {}
}
