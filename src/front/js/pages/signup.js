import React, { useContext } from "react";
import { Context } from "../store/appContext";
import rigoImageUrl from "../../img/rigo-baby.jpg";
import "../../styles/home.css";

export const SignUp = () => {
    const { store, actions } = useContext(Context);

    /*    const fetchGenerico = async (endpoint, data, metodo) => {
           let url = process.env.URL_BACKEND
           let response = await fetch(url + endpoint, {
               method: metodo,
               headers: { "Content-Type": "application/json" },
               body: JSON.stringify(data)
           })
           return response;
       } */

    const registro = async (e) => {
        e.preventDefault();
        console.log("entre en la función");

        const data = new FormData(e.target);
        console.log(data.get("password"))
        let email = data.get("email")
        let password = data.get("password")

        let url = process.env.URL_BACKEND
        let obj = {
            email: email,
            password: password
        }

        let response = await actions.fetchGenerico("signup", obj, "POST")


        if (response.ok) {
            console.log(response.statusText)
            response = await response.json()
            alert(response.message)
        } else {
            alert("No se pudo registrar")
            return
        }

    }

    return (
        <>
            <div className="container">
                <form onSubmit={(e) => registro(e)}>
                    <div className="row d-flex">
                        <div className="col">
                            <div className="row">
                                <h1>Email</h1>
                            </div>
                            <div className="row">
                                <input name="email" placeholder="Escriba aquí su usuario" type="email" />
                            </div>
                            <div className="row">
                                <h1>Password</h1>
                            </div>
                            <div className="row">
                                <input name="password" placeholder="Escriba aquí su clave" type="string" />
                            </div>

                        </div>
                        <div className="col">
                            <div className="row">
                                <button className="btn btn-outline-success"
                                    type="submit"
                                >
                                    Registrar
                                </button>
                            </div>

                        </div>
                        <div className="col"></div>
                    </div>
                </form>
            </div>
        </>
    );
};
