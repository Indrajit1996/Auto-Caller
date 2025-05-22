import styles from './TopbarContent.module.css';

const MenuItem = ({ screen, index, currentScreen, onClick }) => {
  const selected = currentScreen === index + 1;

  return (
    <div
      onClick={() => onClick(index)}
      className={`${styles.tab} ${selected ? styles.selected : ''}`}
    >
      <img
        alt={screen.title}
        src={selected ? screen.selectedIcon : screen.icon}
        className={styles.tabMedia}
      />
      {screen.title}
    </div>
  );
};

export default MenuItem;
