import { Form, type IFormContent } from '../Form/Form';
import './RegisterForm.css';

interface IRegisterForm {
    className?: string
}

const RegisterForm = ({ className="" }: IRegisterForm) => {
    const content: IFormContent = [
        {
            label: { text: "Email" },
            input: {
                type: "email",
                name: "email",
                placeholder: "example@email.com",
                id: "email"
            }
        },
        {
            label: { text: "Username" },
            input: {
                type: "text",
                name: "username",
                placeholder: "User123",
                id: "username"
            }
        },
        {
            label: { text: "Password" },
            input: {
                type: "password",
                name: "password",
                placeholder: "Enter your password",
                id: "password"
            }
        },
        {
            label: { text: "Confirm Password" },
            input: {
                type: "password",
                name: "confirm-password",
                placeholder: "Enter your password again",
                id: "confirmPassword"
            }
        }
    ];
    
    return <Form className={ className } submitBtnName="Sign Up" content={ content } />;
};

export default RegisterForm;
