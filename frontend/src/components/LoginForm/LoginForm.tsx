import { Form, type IFormContent } from '../Form/Form.tsx';
import './LoginForm.css';

interface ILoginForm {
    className?: string
}

const LoginForm = ({ className="" }: ILoginForm) => {
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
            label: { text: "Password" },
            input: {
                type: "password",
                name: "password",
                placeholder: "Enter your password",
                id: "password"
            }
        }
    ];

    return <Form className={ className } submitBtnName="Sign In" content={ content } />;
};

export default LoginForm;
