import RegisterForm from "../../components/RegisterForm/RegisterForm";

interface IRegisterContainer {
    className?: string
}

const RegisterContainer = ({ className="" }: IRegisterContainer) => {
    return (
        <RegisterForm className={ className } />
    );
};

export default RegisterContainer;
