import LoginForm from "../../components/LoginForm/LoginForm";

interface ILoginContainer {
    className?: string
}

const LoginContainer = ({ className="" }: ILoginContainer) => {
    return (
        <LoginForm className={ className } />
    );
};

export default LoginContainer;
