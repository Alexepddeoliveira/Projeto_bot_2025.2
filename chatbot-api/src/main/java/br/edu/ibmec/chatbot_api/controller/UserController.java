package br.edu.ibmec.chatbot_api.controller;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import br.edu.ibmec.chatbot_api.models.User;
import br.edu.ibmec.chatbot_api.repository.IuserRepositorio;

@RestController
@RequestMapping("/users")
public class UserController {

    @Autowired
    private IuserRepositorio Repository;

    @GetMapping()
    public ResponseEntity<List<User>> getUser() {
        List<User> response = Repository.findAll();
        return new ResponseEntity <> (response, HttpStatus.OK);
    }

}
