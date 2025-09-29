package br.edu.ibmec.chatbot_api.models;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.Data;

@Data
@Entity
public class User {
    @Id
    private int id;
    @Column
    private String name;
    @Column
    private String email;
    @Column
    private String cpf;
    @Column
    private String password;

}
