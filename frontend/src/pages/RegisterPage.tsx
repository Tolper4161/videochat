import './Auth.css';
import logoLargeImg from '../assets/img/logo-large.svg';
import RegisterContainer from '../containers/RegisterContainer/RegisterContainer';

const RegisterPage = () => {
    return (
        <section className="auth">
            <div className="auth__content">
                <div className="auth__left">
                    <h1 className="auth__title">Welcome Back</h1>
                    <RegisterContainer className="auth__form" />
                    <span className="auth__">
                        You haven’t an account yet? <a className="auth__link" href="./register.html">Sign up</a>
                    </span>
                </div>
                <div className="auth__right">
                    <img src={ logoLargeImg } alt="large logo" className="auth-logo" />
                </div>
            </div>
        </section>
    );
};

export default RegisterPage;
