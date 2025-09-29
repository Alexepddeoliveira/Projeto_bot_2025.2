package br.edu.ibmec.chatbot_api.repository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import br.edu.ibmec.chatbot_api.models.User;


@Repository
public interface IuserRepositorio extends JpaRepository<User, Integer> {

}
